from rest_framework import serializers

from apps.comptes.models import Professionnel

from .models import DemandeContact


class DemandeContactEcritureSerializer(serializers.ModelSerializer):
    professionnel = serializers.PrimaryKeyRelatedField(queryset=Professionnel.objects.all())

    class Meta:
        model = DemandeContact
        fields = ['id', 'professionnel', 'message', 'statut', 'date']
        read_only_fields = ['statut', 'date']

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user.utilisateur
        return super().create(validated_data)
