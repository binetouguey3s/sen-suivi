import logging

from django.db.models import Count, Max, OuterRef, Subquery
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.permissions import EstUtilisateur
from apps.comptes.personne_confiance import alerter_automatiquement
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
    MessageVocalSerializer,
    NouvelleConversationSerializer,
    ReponseVocaleSerializer,
)
from .services import AudioRefuse, MicroserviceIAIndisponible, synthetiser, traiter_message, transcrire
from .signalement import signaler_equipe
from .vocal import AudioEnMemoireUploadHandler, jeton_vocal, jeton_vocal_valide

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
        return self.repondre(request, entree.validated_data)

    def repondre(self, request, donnees, supplement=None):
        """Pipeline complet d'un message, qu'il ait été tapé ou dit à voix haute."""
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
                    **(supplement or {}),
                },
                status=503,
            )

        conversation_id = self._conserver_si_necessaire(request, donnees, resultat)
        resultat = {
            **resultat,
            **self._orientation(request, donnees, resultat),
            'jeton_vocal': jeton_vocal(resultat['reponse']),
            **(supplement or {}),
        }

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
        supplement = {}
        besoins = None
        if resultat.get('urgence'):
            nature = resultat.get('nature_detresse')
            # Mise en relation gratuite, sans écran de paiement
            supplement['jeton_urgence'] = emettre_jeton(utilisateur)
            textes = [e['contenu'] for e in donnees['historique'] if e['auteur'] == 'UTILISATEUR'] + [donnees['message']]
            # Risque vital ou danger pour autrui, avec l'accord donné à l'avance : la
            # personne de confiance est prévenue, sauf si le message la vise. Jamais
            # pour des violences subies : l'auteur peut être un proche.
            prevenue = self._alerter_personne_confiance(utilisateur, nature, textes)
            supplement['personne_confiance_prevenue'] = prevenue
            # L'équipe Sen Suivi est prévenue de toute situation grave
            self._signaler_equipe(utilisateur, nature, prevenue)
            # Un professionnel adapté reste proposé, en plus des numéros d'urgence
            besoins = ['VIOLENCES'] if nature == 'VIOLENCES' else ['CRISE']
        elif not resultat.get('orientation_professionnel'):
            return {}
        textes = [e['contenu'] for e in donnees['historique'] if e['auteur'] == 'UTILISATEUR'] + [donnees['message']]
        try:
            suggestion = suggerer(utilisateur, textes=textes, besoins=besoins)
        except Exception:  # la suggestion est un confort : son échec ne bloque jamais la réponse
            journal.exception("Suggestion d'orientation indisponible")
            return supplement
        if suggestion is None:
            return supplement
        pro = suggestion.professionnel
        return {
            **supplement,
            'professionnel_suggere': {
                'id': pro.pk,
                'nom': pro.nom,
                'specialite_affichee': pro.get_specialite_display(),
                'ville': pro.ville,
                'raison': suggestion.raison,
            }
        }

    def _alerter_personne_confiance(self, utilisateur, nature, textes):
        try:
            return alerter_automatiquement(utilisateur, nature, textes)
        except Exception:  # l'alerte est un filet de plus : son échec ne retarde jamais la réponse d'urgence
            journal.exception('Alerte automatique à la personne de confiance impossible')
            return None

    def _signaler_equipe(self, utilisateur, nature, prevenue):
        try:
            signaler_equipe(utilisateur, nature, prevenue)
        except Exception:  # même règle : jamais au détriment de la réponse d'urgence
            journal.exception("Signalement à l'équipe impossible")

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



class ChatbotVocalView(ChatbotMessageView):
    """POST /api/chatbot/message-vocal — l'utilisateur parle, Titou répond.

    Audio -> transcription -> EXACTEMENT le même pipeline qu'un message tapé
    (détresse d'abord, puis intention, ressources, génération, validation,
    repli). La transcription est renvoyée pour que la personne voie ce qui a
    été compris, et n'est conservée qu'avec le même consentement que le texte.
    L'audio reste en mémoire et disparaît avec la requête.
    """

    parser_classes = [MultiPartParser]

    def post(self, request):
        # Avant toute lecture du corps : l'audio ne doit jamais toucher le disque
        request._request.upload_handlers = [AudioEnMemoireUploadHandler(request._request)]
        entree = MessageVocalSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        donnees = entree.validated_data
        audio = donnees.pop('audio').read()

        try:
            transcrit = transcrire(audio)
        except AudioRefuse as erreur:
            return Response({'detail': str(erreur)}, status=422)
        except MicroserviceIAIndisponible:
            return Response(
                {'detail': "Le mode vocal n'est pas disponible pour le moment : vous pouvez écrire votre message."},
                status=503,
            )
        finally:
            del audio

        texte = transcrit.get('transcription', '')
        if not transcrit.get('comprise'):
            # Jamais deviner ce qui a été dit : on invite à réessayer ou à écrire
            reponse = transcrit.get('reponse_incomprise') or "Je n'ai pas bien entendu. Pouvez-vous réessayer ?"
            return Response({
                'reponse': reponse, 'source_reponse': None, 'urgence': False, 'intention': None, 'ressource': None,
                'conversation_id': donnees.get('conversation_id'), 'transcription': '', 'jeton_vocal': jeton_vocal(reponse),
            })
        return self.repondre(request, {**donnees, 'message': texte[:2000]}, {'transcription': texte})


class ReponseVocaleView(APIView):
    """POST /api/chatbot/reponse-vocale — lit à voix haute une réponse de Titou.

    Seule une réponse produite et validée par le chatbot peut être lue (jeton
    signé). 204 si la synthèse échoue : l'interface garde le texte, et peut
    utiliser la voix du navigateur.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        entree = ReponseVocaleSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        texte = entree.validated_data['texte']
        if not jeton_vocal_valide(texte, entree.validated_data['jeton_vocal']):
            return Response({'detail': 'Seules les réponses de Titou peuvent être lues à voix haute.'}, status=403)
        audio = synthetiser(texte)
        if audio is None:
            return Response(status=204)
        return HttpResponse(audio, content_type='audio/mpeg')


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
