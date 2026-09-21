"""Création de notifications (pas d'envoi réel d'e-mail en développement)."""

import logging

import httpx
from django.conf import settings

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


logger = logging.getLogger(__name__)


def declencher_workflow(nom, donnees=None):
    """Prévient n8n qu'un événement métier vient de se produire (webhook).

    Best-effort : si n8n est arrêté, l'action de l'utilisateur ne doit jamais
    échouer pour autant.
    """
    try:
        httpx.post(f'{settings.N8N_WEBHOOK_URL}/webhook/{nom}', json=donnees or {}, timeout=3)
    except httpx.HTTPError:
        logger.warning("Workflow n8n « %s » non déclenché (n8n injoignable).", nom)
