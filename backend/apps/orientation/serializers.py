from rest_framework import serializers

from apps.comptes.serializers import ProfessionnelPublicSerializer

from .models import MoyenPaiement


class SuggestionSerializer(serializers.Serializer):
    professionnel = ProfessionnelPublicSerializer()
    raison = serializers.CharField()
    besoins = serializers.ListField(child=serializers.CharField())


class DemandePaiementSerializer(serializers.Serializer):
    # L'accès offert se donne depuis l'administration, jamais par ce formulaire
    moyen = serializers.ChoiceField(choices=[m for m in MoyenPaiement.choices if m[0] != MoyenPaiement.OFFERT])
    telephone = serializers.RegexField(r'^(\+221)?\s?7[05678](\s?\d){7}$', error_messages={
        'invalid': 'Indiquez un numéro sénégalais valide (ex. 77 123 45 67).'
    })
