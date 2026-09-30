"""Forum : PublicationForum et CommentaireForum, tous deux modérés avant affichage,
et ModerationMessage, la trace de chaque décision de modération (IA ou humaine)."""

from django.db import models


class StatutModeration(models.TextChoices):
    # EN_ATTENTE ajoutée le 17/09/2026 : MASQUE signifie « retiré par un
    # modérateur », ce qui n'est pas la même chose qu'« en attente de
    # relecture ». La modération est a priori : rien n'est visible avant
    # validation.
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VISIBLE = 'VISIBLE', 'Visible'
    MASQUE = 'MASQUE', 'Masqué'
    SUPPRIME = 'SUPPRIME', 'Supprimé'
    # Refusé par la modération automatique ; l'auteur peut demander un réexamen
    BLOQUE = 'BLOQUE', 'Bloqué'


class ThematiqueForum(models.TextChoices):
    """Filtres du forum (maquette « Espace d'échange »)."""

    STRESS = 'STRESS', 'Stress'
    SOMMEIL = 'SOMMEIL', 'Sommeil'
    RELATIONS = 'RELATIONS', 'Relations'
    TRAVAIL = 'TRAVAIL', 'Travail'
    DEUIL = 'DEUIL', 'Deuil'


class PublicationForum(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='publications_forum',
        verbose_name='utilisateur',
    )
    moderateur = models.ForeignKey(
        'comptes.Administrateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publications_moderees',
        verbose_name='modérateur',
    )
    # Ajouté suite à la correction du diagramme de classes : titre et thématique.
    titre = models.CharField('titre', max_length=150)
    contenu = models.TextField('contenu')
    thematique = models.CharField(
        'thématique', max_length=10, choices=ThematiqueForum.choices
    )
    date = models.DateTimeField('date', auto_now_add=True)
    statut_moderation = models.CharField(
        'statut de modération',
        max_length=10,
        choices=StatutModeration.choices,
        default=StatutModeration.EN_ATTENTE,
    )

    class Meta:
        verbose_name = 'publication du forum'
        verbose_name_plural = 'publications du forum'
        ordering = ['-date']

    def __str__(self):
        return f'{self.titre} — {self.get_statut_moderation_display()}'


class CommentaireForum(models.Model):
    """Réponse à une publication (relation « contient » du diagramme).

    Le diagramme ne relie pas explicitement un auteur à CommentaireForum ;
    un commentaire anonyme sans auteur n'aurait pas de sens (pseudonyme à
    afficher, modération à tracer), le champ utilisateur est donc ajouté ici
    par cohérence avec PublicationForum.
    """

    publication = models.ForeignKey(
        PublicationForum,
        on_delete=models.CASCADE,
        related_name='commentaires',
        verbose_name='publication',
    )
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='commentaires_forum',
        verbose_name='utilisateur',
    )
    moderateur = models.ForeignKey(
        'comptes.Administrateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='commentaires_moderes',
        verbose_name='modérateur',
    )
    contenu = models.TextField('contenu')
    date = models.DateTimeField('date', auto_now_add=True)
    statut_moderation = models.CharField(
        'statut de modération',
        max_length=10,
        choices=StatutModeration.choices,
        default=StatutModeration.EN_ATTENTE,
    )

    class Meta:
        verbose_name = 'commentaire du forum'
        verbose_name_plural = 'commentaires du forum'
        ordering = ['date']

    def __str__(self):
        return f'Commentaire de {self.utilisateur} sur « {self.publication.titre} »'


class DecisionModeration(models.TextChoices):
    PUBLIER = 'PUBLIER', 'Publié'
    PUBLIER_ACCOMPAGNER = 'PUBLIER_ACCOMPAGNER', 'Publié et accompagné'
    BLOQUER = 'BLOQUER', 'Bloqué'
    BLOQUER_PRIORITAIRE = 'BLOQUER_PRIORITAIRE', 'Bloqué, priorité haute'
    BLOQUER_SILENCIEUX = 'BLOQUER_SILENCIEUX', 'Bloqué sans message (spam)'
    ATTENTE_HUMAINE = 'ATTENTE_HUMAINE', 'En attente de validation humaine'


class DecisionHumaine(models.TextChoices):
    PUBLIER = 'PUBLIER', 'Publié par un administrateur'
    BLOQUER = 'BLOQUER', 'Bloqué par un administrateur'
    CLASSER = 'CLASSER', 'Vu, aucune action'


DECISIONS_BLOQUANTES = [
    DecisionModeration.BLOQUER,
    DecisionModeration.BLOQUER_PRIORITAIRE,
    DecisionModeration.BLOQUER_SILENCIEUX,
]


class ModerationMessage(models.Model):
    """Décision de modération d'une publication ou d'un commentaire.

    Tout est tracé : ce que l'IA a décidé et pourquoi, ce qu'un administrateur
    en a pensé, et la contestation éventuelle de l'auteur. Une décision
    automatique peut toujours être contestée et infirmée.
    """

    publication = models.ForeignKey(
        PublicationForum, on_delete=models.CASCADE, null=True, blank=True, related_name='moderations',
        verbose_name='publication',
    )
    commentaire = models.ForeignKey(
        CommentaireForum, on_delete=models.CASCADE, null=True, blank=True, related_name='moderations',
        verbose_name='commentaire',
    )
    decision = models.CharField('décision automatique', max_length=20, choices=DecisionModeration.choices)
    categorie = models.CharField('catégorie', max_length=24)
    gravite = models.PositiveSmallIntegerField('gravité', default=0)
    raison = models.CharField('raison', max_length=255, blank=True)
    extrait = models.CharField('extrait', max_length=500, blank=True)
    # REGLES (niveau 0), MODELE (niveau 1) ou REPLI (modèle indisponible)
    niveau = models.CharField('niveau', max_length=10)
    # Message montré à l'auteur (pédagogique en cas de blocage, soutien en cas de détresse)
    message_auteur = models.TextField("message à l'auteur", blank=True)
    date = models.DateTimeField('date', auto_now_add=True)

    # File des administrateurs
    a_traiter = models.BooleanField('dans la file des administrateurs', default=False)
    priorite = models.PositiveSmallIntegerField('priorité', default=0)

    # Droit de contestation de l'auteur
    motif_contestation = models.TextField('motif de contestation', blank=True)
    date_contestation = models.DateTimeField('date de contestation', null=True, blank=True)

    # Décision humaine, qui l'emporte toujours sur celle de l'IA
    decision_humaine = models.CharField(
        'décision humaine', max_length=10, choices=DecisionHumaine.choices, blank=True
    )
    moderateur = models.ForeignKey(
        'comptes.Administrateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='decisions_moderation', verbose_name='modérateur',
    )
    date_traitement = models.DateTimeField('date de traitement', null=True, blank=True)

    class Meta:
        verbose_name = 'décision de modération'
        verbose_name_plural = 'décisions de modération'
        ordering = ['-priorite', 'date']

    def __str__(self):
        return f'{self.get_decision_display()} — {self.categorie}'

    @property
    def objet(self):
        return self.publication or self.commentaire

    @property
    def infirmee(self) -> bool:
        """Un administrateur a publié ce que l'IA avait bloqué : un faux positif."""
        return self.decision in DECISIONS_BLOQUANTES and self.decision_humaine == DecisionHumaine.PUBLIER
