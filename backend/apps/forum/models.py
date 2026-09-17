"""Forum : PublicationForum, modérée avant affichage."""

from django.db import models


class StatutModeration(models.TextChoices):
    # EN_ATTENTE ajoutée le 17/09/2026 : MASQUE signifie « retiré par un
    # modérateur », ce qui n'est pas la même chose qu'« en attente de
    # relecture ». La modération est a priori (docs/SPECIFICATIONS.md
    # section 1) : rien n'est visible avant validation.
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VISIBLE = 'VISIBLE', 'Visible'
    MASQUE = 'MASQUE', 'Masqué'
    SUPPRIME = 'SUPPRIME', 'Supprimé'


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
    contenu = models.TextField('contenu')
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
        return f'Publication de {self.utilisateur} — {self.get_statut_moderation_display()}'
