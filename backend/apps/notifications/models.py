"""Notifications : base abstraite Notification, NotificationEmail, NotificationPush.

Contrairement à CompteUtilisateur, Notification n'a pas besoin d'être le
AUTH_USER_MODEL : elle peut donc rester réellement abstraite (abstract=True),
fidèle au diagramme de classes. NotificationEmail et NotificationPush ont
chacune leur propre table complète, avec les champs communs dupliqués.
"""

from django.conf import settings
from django.db import models


class StatutNotification(models.TextChoices):
    ENVOYEE = 'ENVOYEE', 'Envoyée'
    LUE = 'LUE', 'Lue'
    ECHOUEE = 'ECHOUEE', 'Échouée'


class Notification(models.Model):
    # Destinataire typé CompteUtilisateur (et non Utilisateur) : un professionnel
    # (validation de compte) ou un administrateur (nouvelle inscription pro) en
    # reçoivent aussi, pas seulement les utilisateurs.
    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        verbose_name='destinataire',
    )
    contenu = models.TextField('contenu')
    date_envoi = models.DateTimeField("date d'envoi", auto_now_add=True)
    statut = models.CharField(
        'statut',
        max_length=10,
        choices=StatutNotification.choices,
        default=StatutNotification.ENVOYEE,
    )

    class Meta:
        abstract = True
        ordering = ['-date_envoi']


class NotificationEmail(Notification):
    adresse_email = models.EmailField('adresse email')
    objet = models.CharField('objet', max_length=200)

    class Meta:
        verbose_name = 'notification email'
        verbose_name_plural = 'notifications email'
        ordering = ['-date_envoi']

    def __str__(self):
        return f'Email à {self.adresse_email} — {self.objet}'


class NotificationPush(Notification):
    device_token = models.CharField("jeton de l'appareil", max_length=255)

    class Meta:
        verbose_name = 'notification push'
        verbose_name_plural = 'notifications push'
        ordering = ['-date_envoi']

    def __str__(self):
        return f'Push vers {self.destinataire}'
