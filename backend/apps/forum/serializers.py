from rest_framework import serializers

from .models import PublicationForum, StatutModeration


class PublicationForumLectureSerializer(serializers.ModelSerializer):
    # CLAUDE.md section 8 : jamais nom, prenom ni email dans un sérialiseur
    # de publication. Uniquement le pseudonyme.
    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)

    class Meta:
        model = PublicationForum
        fields = ['id', 'pseudonyme', 'contenu', 'date', 'statut_moderation']


class PublicationForumEcritureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationForum
        fields = ['id', 'contenu']

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user.utilisateur
        # Modération a priori : rien n'est visible avant validation
        # (docs/SPECIFICATIONS.md section 1), déjà le défaut du modèle.
        validated_data['statut_moderation'] = StatutModeration.EN_ATTENTE
        return super().create(validated_data)
