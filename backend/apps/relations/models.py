"""Relations : DemandeContact, entre un Utilisateur et un Professionnel, et la
messagerie privée qui s'ouvre entre eux une fois la demande acceptée."""

from django.db import models
from django.utils import timezone


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
    message = models.TextField('message', blank=True)
    # Ajouté suite à la correction du diagramme de classes.
    date_reponse = models.DateTimeField('date de réponse', null=True, blank=True)

    class Meta:
        verbose_name = 'demande de contact'
        verbose_name_plural = 'demandes de contact'
        ordering = ['-date']

    def __str__(self):
        return f'{self.utilisateur} → {self.professionnel} ({self.get_statut_display()})'

    def _repondre(self, statut):
        if self.statut != StatutDemandeContact.EN_ATTENTE:
            raise ValueError('Cette demande a déjà reçu une réponse.')
        self.statut = statut
        self.date_reponse = timezone.now()
        self.save(update_fields=['statut', 'date_reponse'])

    def accepter(self):
        """Le professionnel accepte : son identité reste masquée jusque-là."""
        from apps.notifications.services import notifier

        self._repondre(StatutDemandeContact.ACCEPTEE)
        notifier(
            self.utilisateur,
            'Votre demande a été acceptée',
            f"{self.professionnel.nom} a accepté votre demande d'échange. Vous pouvez désormais lui écrire "
            "dans « Mes demandes », en toute confidentialité.",
        )

    def refuser(self):
        from apps.notifications.services import notifier

        self._repondre(StatutDemandeContact.REFUSEE)
        notifier(
            self.utilisateur,
            "Votre demande n'a pas pu être acceptée",
            f"{self.professionnel.nom} ne peut pas donner suite à votre demande pour le moment.",
        )


class MessageRelation(models.Model):
    """Message privé entre l'utilisateur et le professionnel d'une demande acceptée.

    L'échange reste dans Sen Suivi : ni l'un ni l'autre n'a besoin de partager
    son e-mail ou son téléphone. Personne d'autre ne peut le lire, pas même
    l'administration depuis l'interface.
    """

    demande = models.ForeignKey(
        DemandeContact, on_delete=models.CASCADE, related_name='messages', verbose_name='demande'
    )
    auteur = models.ForeignKey(
        'comptes.CompteUtilisateur', on_delete=models.CASCADE, related_name='messages_relation', verbose_name='auteur'
    )
    contenu = models.TextField('contenu', max_length=2000)
    date = models.DateTimeField('date', auto_now_add=True)
    # Lu par le destinataire ; vide tant qu'il n'a pas ouvert la conversation
    lu_le = models.DateTimeField('lu le', null=True, blank=True)

    class Meta:
        verbose_name = 'message de mise en relation'
        verbose_name_plural = 'messages de mise en relation'
        ordering = ['date', 'id']

    def __str__(self):
        return f'{self.auteur} — {self.date:%d/%m/%Y %H:%M}'
