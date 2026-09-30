"""Accès à la mise en relation après l'offre de lancement.

Seule la mise en relation peut devenir payante. Le chatbot, l'urgence, le
journal, les tests, la bibliothèque, les lieux, le forum et la consultation
des profils restent gratuits pour toujours (voir acces.py).
"""

from django.db import models
from django.utils import timezone


class MoyenPaiement(models.TextChoices):
    WAVE = 'WAVE', 'Wave'
    ORANGE_MONEY = 'ORANGE_MONEY', 'Orange Money'
    FREE_MONEY = 'FREE_MONEY', 'Free Money'
    # Accès offert par l'administration (bourse, partenariat, geste solidaire)
    OFFERT = 'OFFERT', 'Offert par Sen Suivi'


class StatutAcces(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente de paiement'
    ACTIF = 'ACTIF', 'Actif'
    ECHEC = 'ECHEC', 'Échec du paiement'


class AccesMiseEnRelation(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='acces_mise_en_relation',
        verbose_name='utilisateur',
    )
    moyen = models.CharField('moyen de paiement', max_length=12, choices=MoyenPaiement.choices)
    statut = models.CharField('statut', max_length=10, choices=StatutAcces.choices, default=StatutAcces.EN_ATTENTE)
    date_debut = models.DateField('début', default=timezone.localdate)
    date_fin = models.DateField('fin')
    # Référence de la transaction chez le prestataire, le jour où il sera branché
    reference = models.CharField('référence', max_length=100, blank=True)
    date_creation = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'accès à la mise en relation'
        verbose_name_plural = 'accès à la mise en relation'
        ordering = ['-date_creation']

    def __str__(self):
        return f'{self.utilisateur} — {self.get_statut_display()} jusqu’au {self.date_fin}'
