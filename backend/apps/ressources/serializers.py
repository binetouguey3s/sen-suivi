from rest_framework import serializers

from .models import Favori, LieuDetente, Ressource


class RessourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ressource
        fields = [
            'id', 'titre', 'type_ressource', 'contenu', 'thematique',
            'duree_lecture', 'date_publication',
        ]


class LieuDetenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LieuDetente
        fields = [
            'id', 'nom', 'ville', 'description', 'categorie',
            'latitude', 'longitude', 'acces_libre',
        ]


class FavoriEcritureSerializer(serializers.Serializer):
    ressource = serializers.PrimaryKeyRelatedField(queryset=Ressource.objects.all())

    def create(self, validated_data):
        favori, _ = Favori.objects.get_or_create(
            utilisateur=self.context['request'].user.utilisateur,
            ressource=validated_data['ressource'],
        )
        return favori

    def to_representation(self, instance):
        return {'ressource': instance.ressource_id}
