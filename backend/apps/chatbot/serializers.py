from rest_framework import serializers

from .models import MessageChatbot


class MessageEntreeSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000, trim_whitespace=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    # Vrai uniquement si l'utilisateur connecté a explicitement accepté de
    # conserver cet échange dans son historique
    # (voir ConversationChatbot.consentement_conservation).
    consentement_conservation = serializers.BooleanField(required=False, default=False)

    def validate_message(self, valeur):
        if not valeur.strip():
            raise serializers.ValidationError('Le message ne peut pas être vide.')
        return valeur.strip()


class RessourceSuggereeSerializer(serializers.Serializer):
    ressource_id = serializers.IntegerField()
    titre = serializers.CharField()
    thematique = serializers.CharField()


class MessageSortieSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    reponse = serializers.CharField()
    source_reponse = serializers.CharField(allow_null=True)
    urgence = serializers.BooleanField()
    intention = serializers.CharField(allow_null=True)
    ressource = RessourceSuggereeSerializer(allow_null=True)


# --- Historique des conversations conservées ---------------------------------

LONGUEUR_APERCU = 80
MESSAGES_ANTERIEURS_MAX = 50


class MessageHistoriqueSerializer(serializers.ModelSerializer):
    """Un message tel qu'il s'affichait dans le chat."""

    auteur = serializers.CharField(source='type_expediteur')
    ressource = serializers.SerializerMethodField()

    class Meta:
        model = MessageChatbot
        fields = ['id', 'auteur', 'contenu', 'date_envoi', 'urgence', 'ressource']

    def get_ressource(self, message):
        if message.ressource is None:
            return None
        return {
            'ressource_id': message.ressource_id,
            'titre': message.ressource.titre,
            'thematique': message.ressource.thematique,
        }


class ConversationResumeSerializer(serializers.Serializer):
    """Ligne de la liste de l'historique : date et début du premier message."""

    id = serializers.IntegerField()
    date = serializers.DateTimeField()
    derniere_activite = serializers.DateTimeField()
    nombre_messages = serializers.IntegerField()
    apercu = serializers.SerializerMethodField()

    def get_apercu(self, conversation):
        premier = conversation.premier_message or ''
        return premier if len(premier) <= LONGUEUR_APERCU else premier[:LONGUEUR_APERCU].rstrip() + '…'


class MessageAnterieurSerializer(serializers.Serializer):
    """Message échangé avant que l'utilisateur coche « Conserver cet échange »."""

    auteur = serializers.ChoiceField(choices=['UTILISATEUR', 'BOT'])
    contenu = serializers.CharField(max_length=2000)
    urgence = serializers.BooleanField(required=False, default=False)
    ressource_id = serializers.IntegerField(required=False, allow_null=True)


class NouvelleConversationSerializer(serializers.Serializer):
    """Enregistre d'un coup la conversation en cours, au moment du consentement."""

    messages = MessageAnterieurSerializer(many=True, allow_empty=False, max_length=MESSAGES_ANTERIEURS_MAX)
