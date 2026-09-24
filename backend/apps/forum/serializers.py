from rest_framework import serializers

from .models import CommentaireForum, PublicationForum, StatutModeration


class CommentaireForumLectureSerializer(serializers.ModelSerializer):
    # Anonymat du forum : jamais nom, prenom ni email dans un sérialiseur
    # de publication. Uniquement le pseudonyme.
    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)

    class Meta:
        model = CommentaireForum
        fields = ['id', 'pseudonyme', 'contenu', 'date']


class CommentaireForumEcritureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentaireForum
        fields = ['id', 'contenu']

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user.utilisateur
        validated_data['publication'] = self.context['publication']
        # Modération a priori, comme pour les publications : le commentaire
        # n'est visible des autres membres qu'après validation.
        validated_data['statut_moderation'] = StatutModeration.EN_ATTENTE
        return super().create(validated_data)


class PublicationSimilaireSerializer(serializers.ModelSerializer):
    nb_reponses = serializers.SerializerMethodField()

    class Meta:
        model = PublicationForum
        fields = ['id', 'titre', 'nb_reponses']

    def get_nb_reponses(self, publication):
        return publication.commentaires.filter(statut_moderation=StatutModeration.VISIBLE).count()


class PublicationForumLectureSerializer(serializers.ModelSerializer):
    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    nb_reponses = serializers.SerializerMethodField()

    class Meta:
        model = PublicationForum
        fields = ['id', 'pseudonyme', 'titre', 'contenu', 'thematique', 'date', 'nb_reponses']

    def get_nb_reponses(self, publication):
        return publication.commentaires.filter(statut_moderation=StatutModeration.VISIBLE).count()


class PublicationForumDetailSerializer(PublicationForumLectureSerializer):
    commentaires = serializers.SerializerMethodField()
    sujets_similaires = serializers.SerializerMethodField()

    class Meta(PublicationForumLectureSerializer.Meta):
        fields = PublicationForumLectureSerializer.Meta.fields + ['commentaires', 'sujets_similaires']

    def get_commentaires(self, publication):
        visibles = publication.commentaires.filter(statut_moderation=StatutModeration.VISIBLE)
        return CommentaireForumLectureSerializer(visibles, many=True).data

    def get_sujets_similaires(self, publication):
        autres = (
            PublicationForum.objects.filter(
                thematique=publication.thematique, statut_moderation=StatutModeration.VISIBLE
            )
            .exclude(pk=publication.pk)
            .order_by('-date')[:3]
        )
        return PublicationSimilaireSerializer(autres, many=True).data


class PublicationForumEcritureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicationForum
        fields = ['id', 'titre', 'contenu', 'thematique']

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user.utilisateur
        # Modération a priori : rien n'est visible avant validation, déjà le
        # défaut du modèle.
        validated_data['statut_moderation'] = StatutModeration.EN_ATTENTE
        return super().create(validated_data)


# --- Modération (écran d'administration) ------------------------------------


class PublicationForumModerationSerializer(serializers.ModelSerializer):
    """Vue administrateur : toutes les publications, quel que soit leur statut."""

    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    thematique_affichee = serializers.CharField(source='get_thematique_display', read_only=True)

    class Meta:
        model = PublicationForum
        fields = ['id', 'pseudonyme', 'titre', 'contenu', 'thematique', 'thematique_affichee', 'date', 'statut_moderation']


class ModerationSerializer(serializers.Serializer):
    """PATCH générique de modération : fait uniquement transiter le statut."""

    statut_moderation = serializers.ChoiceField(choices=StatutModeration.choices)

    def save(self, **kwargs):
        objet = self.instance
        objet.statut_moderation = self.validated_data['statut_moderation']
        objet.moderateur = self.context['request'].user.administrateur
        objet.save(update_fields=['statut_moderation', 'moderateur'])
        return objet


class CommentaireForumModerationSerializer(serializers.ModelSerializer):
    """Vue administrateur : tous les commentaires, quel que soit leur statut."""

    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    publication_titre = serializers.CharField(source='publication.titre', read_only=True)

    class Meta:
        model = CommentaireForum
        fields = ['id', 'pseudonyme', 'publication', 'publication_titre', 'contenu', 'date', 'statut_moderation']
