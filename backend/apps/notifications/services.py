"""Création de notifications (pas d'envoi réel d'e-mail en développement)."""

from .models import NotificationEmail


def notifier(compte, objet, contenu):
    return NotificationEmail.objects.create(
        destinataire=compte,
        adresse_email=compte.email,
        objet=objet,
        contenu=contenu,
    )
