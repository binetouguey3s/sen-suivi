"""Envoi réel des e-mails, par le serveur SMTP configuré dans le .env.

Sans serveur configuré (développement), les e-mails s'affichent dans les
journaux du back-end au lieu de partir : rien ne casse.
"""

import logging
import threading

from django.conf import settings
from django.core.mail import send_mail

journal = logging.getLogger(__name__)

SIGNATURE = (
    "\n\n—\nSen Suivi, plateforme de prévention et de suivi du bien-être mental.\n"
    "Sen Suivi ne remplace pas un professionnel de santé. En cas de détresse immédiate : "
    "800 805 805 (écoute, gratuit) ou 1515 (SAMU)."
)


def envoyer(adresse: str, objet: str, contenu: str) -> bool:
    """Envoie un e-mail tout de suite ; vrai s'il est parti. Jamais d'exception."""
    try:
        send_mail(objet, contenu + SIGNATURE, settings.DEFAULT_FROM_EMAIL, [adresse], fail_silently=False)
        return True
    except Exception as erreur:  # serveur injoignable, identifiants refusés… l'action continue
        # Jamais l'adresse ni le contenu dans les journaux : seulement le type d'erreur
        journal.warning('E-mail non envoyé : %s', type(erreur).__name__)
        return False


def envoyer_en_arriere_plan(adresse: str, objet: str, contenu: str) -> None:
    """Pour les notifications : la page n'attend jamais le serveur d'e-mails."""
    if settings.EMAIL_ASYNCHRONE:
        threading.Thread(target=envoyer, args=(adresse, objet, contenu), daemon=True).start()
    else:
        envoyer(adresse, objet, contenu)
