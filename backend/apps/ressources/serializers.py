from rest_framework import serializers

from .models import Favori, LieuDetente, Ressource, valider_fichier_audio


class RessourceSerializer(serializers.ModelSerializer):
    # Envoi du fichier (multipart) ; null le retire. Jamais renvoyé tel quel :
    # la lecture passe par `audio`
    fichier_audio = serializers.FileField(
        write_only=True, required=False, allow_null=True, validators=[valider_fichier_audio]
    )
    # Ce que le lecteur doit jouer : le fichier envoyé en priorité, sinon url_audio
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Ressource
        fields = [
            'id', 'titre', 'type_ressource', 'contenu', 'thematique',
            'duree_lecture', 'date_publication', 'url_audio', 'fichier_audio', 'audio',
        ]

    def get_audio(self, ressource) -> str:
        if not ressource.fichier_audio:
            return ressource.url_audio
        requete = self.context.get('request')
        # Adresse complète : le front-end n'est pas servi par le même hôte que Django
        return requete.build_absolute_uri(ressource.fichier_audio.url) if requete else ressource.fichier_audio.url

    def create(self, validated_data):
        if validated_data.get('fichier_audio') is None:
            validated_data.pop('fichier_audio', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'fichier_audio' in validated_data:
            # Remplacé ou retiré : l'ancien fichier ne reste pas sur le disque
            if instance.fichier_audio:
                instance.fichier_audio.delete(save=False)
            if validated_data['fichier_audio'] is None:
                validated_data['fichier_audio'] = ''
        return super().update(instance, validated_data)


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
