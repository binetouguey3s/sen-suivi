from rest_framework import serializers

from .models import Favori, LieuDetente, Ressource, TypeRessource, valider_fichier_audio


class AuteurSerializer(serializers.Serializer):
    """Crédit d'une ressource proposée par un professionnel : jamais son e-mail."""

    id = serializers.IntegerField()
    nom = serializers.CharField()
    specialite_affichee = serializers.CharField(source='get_specialite_display')


class RessourceSerializer(serializers.ModelSerializer):
    # Envoi du fichier (multipart) ; null le retire. Jamais renvoyé tel quel :
    # la lecture passe par `audio`
    fichier_audio = serializers.FileField(
        write_only=True, required=False, allow_null=True, validators=[valider_fichier_audio]
    )
    # Ce que le lecteur doit jouer : le fichier envoyé en priorité, sinon url_audio
    audio = serializers.SerializerMethodField()
    # Seul l'identifiant YouTube sert à intégrer la vidéo, jamais le lien saisi
    video_id = serializers.CharField(read_only=True)
    auteur = AuteurSerializer(read_only=True)

    class Meta:
        model = Ressource
        fields = [
            'id', 'titre', 'type_ressource', 'contenu', 'thematique',
            'duree_lecture', 'date_publication', 'url_audio', 'fichier_audio', 'audio',
            'url_video', 'video_id', 'auteur', 'statut', 'motif_refus', 'date_soumission', 'date_modification',
        ]
        # Le statut ne change que par les actions soumettre / publier / refuser
        read_only_fields = ['statut', 'motif_refus', 'date_soumission', 'date_modification']

    def validate(self, attrs):
        type_ressource = attrs.get('type_ressource', getattr(self.instance, 'type_ressource', None))
        url_video = attrs.get('url_video', getattr(self.instance, 'url_video', ''))
        if type_ressource == TypeRessource.VIDEO and not url_video:
            raise serializers.ValidationError({'url_video': 'Une vidéo a besoin de son lien YouTube.'})
        return attrs

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


class RessourceProSerializer(RessourceSerializer):
    """Brouillon du professionnel : il peut être enregistré incomplet (sauvegarde
    automatique). Tout est vérifié au moment de la soumission."""

    class Meta(RessourceSerializer.Meta):
        extra_kwargs = {
            'titre': {'allow_blank': True},
            'contenu': {'allow_blank': True},
            'thematique': {'allow_blank': True},
        }

    def validate(self, attrs):
        # Une vidéo sans lien reste un brouillon possible ; le lien saisi, lui,
        # est toujours vérifié (validateur du champ)
        return attrs


class LieuDetenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LieuDetente
        fields = [
            'id', 'nom', 'ville', 'description', 'categorie',
            'latitude', 'longitude', 'acces_libre',
        ]


class FavoriEcritureSerializer(serializers.Serializer):
    # On ne met en favori qu'une ressource publiée
    ressource = serializers.PrimaryKeyRelatedField(queryset=Ressource.objects.filter(statut='PUBLIEE'))

    def create(self, validated_data):
        favori, _ = Favori.objects.get_or_create(
            utilisateur=self.context['request'].user.utilisateur,
            ressource=validated_data['ressource'],
        )
        return favori

    def to_representation(self, instance):
        return {'ressource': instance.ressource_id}
