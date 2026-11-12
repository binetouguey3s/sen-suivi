"""Création des notifications : dans la cloche de l'application et, si un serveur
SMTP est configuré, par e-mail (en respectant les préférences de chacun)."""

import logging
import threading

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
    échouer pour autant. Sans n8n (N8N_WEBHOOK_URL vide, hébergement gratuit),
    Django fait lui-même l'essentiel : voir _sans_n8n.
    """
    if not settings.N8N_WEBHOOK_URL:
        _sans_n8n(nom, donnees or {})
        return
    try:
        httpx.post(f'{settings.N8N_WEBHOOK_URL}/webhook/{nom}', json=donnees or {}, timeout=3)
    except httpx.HTTPError:
        logger.warning("Workflow n8n « %s » non déclenché (n8n injoignable).", nom)


def _sans_n8n(nom, donnees):
    """Mêmes effets que les workflows n8n, sans n8n (mêmes textes que automations/)."""
    from apps.comptes.models import Administrateur, Professionnel

    if nom == 'nouvelle-demande':
        professionnel = Professionnel.objects.filter(pk=donnees.get('professionnel_id')).first()
        if professionnel:
            notifier(
                professionnel,
                'Nouvelle demande de mise en relation',
                f"{donnees.get('pseudonyme')} vous a envoyé une demande de mise en relation. "
                "Rendez-vous dans Demandes pour l'accepter ou la décliner.",
                preference='nouvelle_demande',
            )
    elif nom == 'nouveau-professionnel':
        for administrateur in Administrateur.objects.filter(is_active=True):
            notifier(
                administrateur,
                'Nouvelle inscription professionnelle à valider',
                f"{donnees.get('nom')} ({donnees.get('specialite')}, {donnees.get('ville')}) vient de s'inscrire. "
                'Rendez-vous dans Administration > Professionnels pour valider ou refuser ce profil.',
            )
    elif nom == 'ressource-modifiee':
        from apps.ressources.indexation import reindexer_sans_erreur

        # Le microservice peut mettre une minute à se réveiller : la page n'attend pas
        threading.Thread(target=reindexer_sans_erreur, daemon=True).start()
