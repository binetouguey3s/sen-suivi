from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConversationChatbot, MessageChatbot, TypeExpediteur
from .serializers import MessageEntreeSerializer, MessageSortieSerializer
from .services import MicroserviceIAIndisponible, traiter_message


class ChatbotMessageView(APIView):
    """POST /api/chatbot/message — accessible sans authentification (docs/CONTEXTE.md section 5).

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
            resultat = traiter_message(donnees['message'])
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

        sortie = MessageSortieSerializer(data={**resultat, 'conversation_id': conversation_id})
        sortie.is_valid(raise_exception=True)
        return Response(sortie.validated_data)

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
        MessageChatbot.objects.create(
            conversation=conversation,
            contenu=resultat['reponse'],
            type_expediteur=TypeExpediteur.BOT,
            source_reponse=resultat.get('source_reponse'),
        )
        return conversation.id
