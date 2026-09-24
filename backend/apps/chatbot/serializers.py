from rest_framework import serializers


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
