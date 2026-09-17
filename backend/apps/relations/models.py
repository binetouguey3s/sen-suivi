"""Relations : DemandeContact, entre un Utilisateur et un Professionnel."""

from django.db import models


class StatutDemandeContact(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    ACCEPTEE = 'ACCEPTEE', 'Acceptée'
    REFUSEE = 'REFUSEE', 'Refusée'


class DemandeContact(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='demandes_contact_envoyees',
        verbose_name='utilisateur',
    )
    professionnel = models.ForeignKey(
        'comptes.Professionnel',
        on_delete=models.CASCADE,
        related_name='demandes_contact_recues',
        verbose_name='professionnel',
    )
    date = models.DateTimeField('date', auto_now_add=True)
    statut = models.CharField(
        'statut',
        max_length=10,
        choices=StatutDemandeContact.choices,
        default=StatutDemandeContact.EN_ATTENTE,
    )
    message = models.TextField('message')

    class Meta:
        verbose_name = 'demande de contact'
        verbose_name_plural = 'demandes de contact'
        ordering = ['-date']

    def __str__(self):
        return f'{self.utilisateur} → {self.professionnel} ({self.get_statut_display()})'
