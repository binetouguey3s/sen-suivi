import logging

from django.db.models import Count, Max, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.permissions import EstUtilisateur
from apps.orientation.services import suggerer
from apps.orientation.urgence import emettre_jeton
from apps.ressources.models import Ressource
from apps.suivi.profil_tendance import a_consenti, profil_tendance

from .models import ConversationChatbot, MessageChatbot, TypeExpediteur
from .serializers import (
    ConversationResumeSerializer,
    MessageEntreeSerializer,
    MessageHistoriqueSerializer,
    MessageSortieSerializer,
    NouvelleConversationSerializer,
)
from .services import MicroserviceIAIndisponible, traiter_message

journal = logging.getLogger(__name__)


class ChatbotMessageView(APIView):
    """POST /api/chatbot/message — accessible sans authentification.

    L'historique n'est enregistré que si le compte est connecté ET a
    explicitement accepté la conservation (ConversationChatbot.consentement_conservation).
    Sans compte ou sans ce consentement, l'échange est traité sans être stocké.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        entree = MessageEntreeSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data

        try:
            resultat = traiter_message(
                donnees['message'], donnees['historique'], self._profil(request), self._suggestion_possible(request)
            )
        except MicroserviceIAIndisponible:
            return Response(
                {
                    'reponse': (
                        "Le chatbot n'est pas disponible pour le moment. En cas de "
                        "détresse immédiate, appelez le 800 805 805 ou le 1515."
                    ),
                    'source_reponse': None,
                    'urgence': False,
                    'intention': None,
                    'ressource': None,
                },
                status=503,
            )

        conversation_id = self._conserver_si_necessaire(request, donnees, resultat)
        resultat = {**resultat, **self._orientation(request, donnees, resultat)}

        sortie = MessageSortieSerializer(data={**resultat, 'conversation_id': conversation_id})
        sortie.is_valid(raise_exception=True)
        return Response(sortie.validated_data)

    def _suggestion_possible(self, request):
        return request.user.is_authenticated and getattr(request.user, 'utilisateur', None) is not None

    def _orientation(self, request, donnees, resultat):
        """Jeton d'urgence en cas de détresse ; sinon, si la personne cherche un
        professionnel, celui que l'algorithme d'orientation met en avant."""
        utilisateur = getattr(request.user, 'utilisateur', None) if request.user.is_authenticated else None
        if utilisateur is None:
            return {}
        if resultat.get('urgence'):
            return {'jeton_urgence': emettre_jeton(utilisateur)}
        if not resultat.get('orientation_professionnel'):
            return {}
        textes = [e['contenu'] for e in donnees['historique'] if e['auteur'] == 'UTILISATEUR'] + [donnees['message']]
        try:
            suggestion = suggerer(utilisateur, textes=textes)
        except Exception:  # la suggestion est un confort : son échec ne bloque jamais la réponse
            journal.exception("Suggestion d'orientation indisponible")
            return {}
        if suggestion is None:
            return {}
        pro = suggestion.professionnel
        return {
            'professionnel_suggere': {
                'id': pro.pk,
                'nom': pro.nom,
                'specialite_affichee': pro.get_specialite_display(),
                'ville': pro.ville,
                'raison': suggestion.raison,
            }
        }

    def _profil(self, request):
        """Profil de tendance d'un utilisateur connecté et consentant ; sinon aucun,
        et le chatbot répond exactement comme sans personnalisation."""
        utilisateur = getattr(request.user, 'utilisateur', None) if request.user.is_authenticated else None
        if not utilisateur or not a_consenti(utilisateur):
            return None
        try:
            return profil_tendance(utilisateur)
        except Exception:  # la personnalisation est un confort : son échec ne bloque jamais la réponse
            journal.exception('Profil de tendance indisponible')
            return None

    def _conserver_si_necessaire(self, request, donnees, resultat):
        utilisateur = getattr(request.user, 'utilisateur', None) if request.user.is_authenticated else None
        if not utilisateur or not donnees['consentement_conservation']:
            return None

        conversation = None
        if donnees.get('conversation_id'):
            conversation = ConversationChatbot.objects.filter(
                pk=donnees['conversation_id'], utilisateur=utilisateur
            ).first()
        if conversation is None:
            conversation = ConversationChatbot.objects.create(
                utilisateur=utilisateur, consentement_conservation=True
            )

        MessageChatbot.objects.create(
            conversation=conversation, contenu=donnees['message'], type_expediteur=TypeExpediteur.UTILISATEUR
        )
        suggestion = resultat.get('ressource') or {}
        MessageChatbot.objects.create(
            conversation=conversation,
            contenu=resultat['reponse'],
            type_expediteur=TypeExpediteur.BOT,
            source_reponse=resultat.get('source_reponse'),
            urgence=bool(resultat.get('urgence')),
            ressource=Ressource.objects.filter(pk=suggestion.get('ressource_id')).first(),
        )
        return conversation.id


def conversations_de(request):
    """Conversations conservées du compte connecté, et d'aucun autre."""
    return ConversationChatbot.objects.filter(
        utilisateur=request.user.utilisateur, consentement_conservation=True
    )


class ConversationsView(APIView):
    """GET  /api/chatbot/conversations — historique, de la plus récente à la plus ancienne.
    POST /api/chatbot/conversations — enregistre la conversation en cours au moment où
    l'utilisateur coche « Conserver cet échange » : les messages déjà échangés ne sont
    pas perdus. Seul l'auteur peut ensuite la lire.
    """

    permission_classes = [EstUtilisateur]

    def get(self, request):
        premier_message = MessageChatbot.objects.filter(
            conversation=OuterRef('pk'), type_expediteur=TypeExpediteur.UTILISATEUR
        ).order_by('date_envoi', 'id').values('contenu')[:1]
        conversations = (
            conversations_de(request)
            .annotate(
                nombre_messages=Count('messages'),
                derniere_activite=Max('messages__date_envoi'),
                premier_message=Subquery(premier_message),
            )
            .filter(nombre_messages__gt=0)
            .order_by('-derniere_activite')
        )
        return Response(ConversationResumeSerializer(conversations, many=True).data)

    def post(self, request):
        entree = NouvelleConversationSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        messages = entree.validated_data['messages']

        ids_suggeres = {m['ressource_id'] for m in messages if m.get('ressource_id')}
        ressources = Ressource.objects.in_bulk(ids_suggeres)
        conversation = ConversationChatbot.objects.create(
            utilisateur=request.user.utilisateur, consentement_conservation=True
        )
        # Créés un par un pour garder l'ordre de la conversation (date d'envoi croissante)
        for m in messages:
            MessageChatbot.objects.create(
                conversation=conversation,
                contenu=m['contenu'],
                type_expediteur=m['auteur'],
                urgence=m['urgence'] and m['auteur'] == TypeExpediteur.BOT,
                ressource=ressources.get(m.get('ressource_id')) if m['auteur'] == TypeExpediteur.BOT else None,
            )
        return Response({'id': conversation.id}, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    """GET    /api/chatbot/conversations/<id> — messages d'une conversation conservée.
    DELETE /api/chatbot/conversations/<id> — efface définitivement la conversation
    (droit à l'effacement). Une conversation d'un autre compte renvoie 404.
    """

    permission_classes = [EstUtilisateur]

    def get(self, request, pk):
        conversation = get_object_or_404(conversations_de(request), pk=pk)
        messages = conversation.messages.select_related('ressource').order_by('date_envoi', 'id')
        return Response(
            {
                'id': conversation.id,
                'date': conversation.date,
                'messages': MessageHistoriqueSerializer(messages, many=True).data,
            }
        )

    def delete(self, request, pk):
        get_object_or_404(conversations_de(request), pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
