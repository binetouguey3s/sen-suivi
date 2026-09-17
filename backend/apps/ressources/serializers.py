from rest_framework import serializers

from .models import LieuDetente, Ressource


class RessourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ressource
        fields = ['id', 'titre', 'type_ressource', 'contenu', 'thematique']


class LieuDetenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LieuDetente
        fields = ['id', 'nom', 'ville', 'description', 'categorie']
