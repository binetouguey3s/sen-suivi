from rest_framework import serializers

from .moderation import derniere_moderation, trancher
from .models import (
    CommentaireForum,
    DecisionHumaine,
    DecisionModeration,
    ModerationMessage,
    PublicationForum,
    StatutModeration,
)


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


class DecisionIASerializer(serializers.ModelSerializer):
    """Ce que la modération automatique a décidé, et pourquoi."""

    decision_affichee = serializers.CharField(source='get_decision_display', read_only=True)

    class Meta:
        model = ModerationMessage
        fields = [
            'id', 'decision', 'decision_affichee', 'categorie', 'gravite', 'raison', 'extrait', 'niveau',
            'date', 'decision_humaine', 'motif_contestation', 'date_contestation',
        ]


class AvecDecisionIA(serializers.Serializer):
    decision_ia = serializers.SerializerMethodField()

    def get_decision_ia(self, objet):
        moderation = derniere_moderation(objet)
        return DecisionIASerializer(moderation).data if moderation else None


class PublicationForumModerationSerializer(AvecDecisionIA, serializers.ModelSerializer):
    """Vue administrateur : toutes les publications, quel que soit leur statut."""

    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    thematique_affichee = serializers.CharField(source='get_thematique_display', read_only=True)

    class Meta:
        model = PublicationForum
        fields = [
            'id', 'pseudonyme', 'titre', 'contenu', 'thematique', 'thematique_affichee', 'date', 'statut_moderation',
            'decision_ia',
        ]


class ModerationSerializer(serializers.Serializer):
    """PATCH générique de modération : fait uniquement transiter le statut."""

    statut_moderation = serializers.ChoiceField(choices=StatutModeration.choices)

    def save(self, **kwargs):
        objet = self.instance
        statut = self.validated_data['statut_moderation']
        administrateur = self.context['request'].user.administrateur
        moderation = derniere_moderation(objet)
        if moderation and statut != StatutModeration.EN_ATTENTE:
            # L'administrateur infirme ou confirme la décision de l'IA : tracé, et
            # une infraction infirmée ne compte plus
            trancher(
                moderation,
                DecisionHumaine.PUBLIER if statut == StatutModeration.VISIBLE else DecisionHumaine.BLOQUER,
                administrateur,
            )
            objet.refresh_from_db()
        objet.statut_moderation = statut
        objet.moderateur = administrateur
        objet.save(update_fields=['statut_moderation', 'moderateur'])
        return objet


class CommentaireForumModerationSerializer(AvecDecisionIA, serializers.ModelSerializer):
    """Vue administrateur : tous les commentaires, quel que soit leur statut."""

    pseudonyme = serializers.CharField(source='utilisateur.pseudonyme', read_only=True)
    publication_titre = serializers.CharField(source='publication.titre', read_only=True)

    class Meta:
        model = CommentaireForum
        fields = [
            'id', 'pseudonyme', 'publication', 'publication_titre', 'contenu', 'date', 'statut_moderation',
            'decision_ia',
        ]


# --- File de modération et suivi par l'auteur --------------------------------


class FileModerationSerializer(serializers.ModelSerializer):
    """Élément de la file des administrateurs : le message, la décision de l'IA
    et la contestation éventuelle, triés par priorité."""

    decision_affichee = serializers.CharField(source='get_decision_display', read_only=True)
    type = serializers.SerializerMethodField()
    objet_id = serializers.SerializerMethodField()
    pseudonyme = serializers.SerializerMethodField()
    titre = serializers.SerializerMethodField()
    contenu = serializers.SerializerMethodField()
    statut_moderation = serializers.SerializerMethodField()

    class Meta:
        model = ModerationMessage
        fields = [
            'id', 'type', 'objet_id', 'pseudonyme', 'titre', 'contenu', 'statut_moderation',
            'decision', 'decision_affichee', 'categorie', 'gravite', 'raison', 'extrait', 'niveau', 'priorite',
            'date', 'motif_contestation', 'date_contestation',
        ]

    def get_type(self, m):
        return 'PUBLICATION' if m.publication_id else 'COMMENTAIRE'

    def get_objet_id(self, m):
        return m.objet.pk

    def get_pseudonyme(self, m):
        return m.objet.utilisateur.pseudonyme

    def get_titre(self, m):
        return m.publication.titre if m.publication_id else m.commentaire.publication.titre

    def get_contenu(self, m):
        return m.objet.contenu

    def get_statut_moderation(self, m):
        return m.objet.statut_moderation


class DecisionAdministrateurSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=DecisionHumaine.choices)


class ContestationSerializer(serializers.Serializer):
    motif = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class MonMessageSerializer(serializers.Serializer):
    """Suivi par l'auteur de ses propres messages : statut, explication, contestation."""

    type = serializers.CharField()
    id = serializers.IntegerField()
    titre = serializers.CharField()
    contenu = serializers.CharField()
    date = serializers.DateTimeField()
    statut_moderation = serializers.CharField()
    message = serializers.CharField()
    peut_contester = serializers.BooleanField()
    conteste = serializers.BooleanField()


def mon_message(objet) -> dict:
    moderation = derniere_moderation(objet)
    bloque = objet.statut_moderation == StatutModeration.BLOQUE
    silencieux = moderation and moderation.decision == DecisionModeration.BLOQUER_SILENCIEUX
    message = ''
    if moderation:
        message = moderation.message_auteur
        if bloque and silencieux:
            message = "Votre message n'a pas été publié : il ressemble à de la publicité ou contient un lien externe."
    return {
        'type': 'PUBLICATION' if isinstance(objet, PublicationForum) else 'COMMENTAIRE',
        'id': objet.pk,
        'titre': objet.titre if isinstance(objet, PublicationForum) else objet.publication.titre,
        'contenu': objet.contenu,
        'date': objet.date,
        'statut_moderation': objet.statut_moderation,
        'message': message,
        'peut_contester': bool(bloque and moderation and not moderation.date_contestation),
        'conteste': bool(moderation and moderation.date_contestation),
    }
