"""Création des notifications : dans la cloche de l'application et, si un serveur
SMTP est configuré, par e-mail (en respectant les préférences de chacun)."""

import logging

import httpx
from django.conf import settings

from .courriel import envoyer_en_arriere_plan
from .models import NotificationEmail

# Les e-mails de sécurité contiennent un lien secret : ils ne s'affichent jamais
# dans le panneau de notifications de l'application.
OBJET_REINITIALISATION = 'Réinitialisation de votre mot de passe Sen Suivi'


def notifier(compte, objet, contenu, preference=None):
    """Notification dans la cloche, et par e-mail sauf si la personne a désactivé
    ce type de notification (`preference`, ex. « reponse_professionnel »)."""
    notification = NotificationEmail.objects.create(
        destinataire=compte,
        adresse_email=compte.email,
        objet=objet,
        contenu=contenu,
    )
    accepte = not preference or (compte.preferences or {}).get(preference, {}).get('email', True)
    # Le statut de la notification sert à « lu / non lu » dans la cloche : un
    # échec d'envoi est seulement journalisé, la notification reste visible
    if settings.EMAIL_NOTIFICATIONS and accepte:
        envoyer_en_arriere_plan(compte.email, objet, contenu)
    return notification


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
