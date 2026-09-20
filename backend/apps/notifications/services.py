"""Création de notifications (pas d'envoi réel d'e-mail en développement)."""

from .models import NotificationEmail

# Les e-mails de sécurité contiennent un lien secret : ils ne s'affichent jamais
# dans le panneau de notifications de l'application.
OBJET_REINITIALISATION = 'Réinitialisation de votre mot de passe Sen Suivi'


def notifier(compte, objet, contenu):
    return NotificationEmail.objects.create(
        destinataire=compte,
        adresse_email=compte.email,
        objet=objet,
        contenu=contenu,
    )
