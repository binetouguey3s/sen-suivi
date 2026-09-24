"""Forum : PublicationForum et CommentaireForum, tous deux modérés avant affichage."""

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
