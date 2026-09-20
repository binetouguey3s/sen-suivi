"""Réinitialisation du mot de passe (route /api/auth/mot-de-passe-oublie)."""

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from apps.notifications.models import NotificationEmail
from apps.notifications.services import OBJET_REINITIALISATION

from .models import CompteUtilisateur


def demander_reinitialisation(email):
    """Envoie un lien de réinitialisation si le compte existe.

    Ne révèle jamais si l'adresse existe : la vue répond toujours de la même façon.
    """
    compte = CompteUtilisateur.objects.filter(email__iexact=email, is_active=True).first()
    if compte is None:
        return
    uid = urlsafe_base64_encode(force_bytes(compte.pk))
    token = default_token_generator.make_token(compte)
    lien = f'{settings.FRONTEND_URL}/nouveau-mot-de-passe?uid={uid}&token={token}'
    NotificationEmail.objects.create(
        destinataire=compte,
        adresse_email=compte.email,
        objet=OBJET_REINITIALISATION,
        contenu=f'Pour choisir un nouveau mot de passe, ouvrez ce lien : {lien}',
    )
    # Pas de serveur SMTP en développement : le lien s'affiche dans les journaux du back-end.
    print(f'[Sen Suivi] Lien de réinitialisation pour {compte.email} : {lien}', flush=True)


def confirmer_reinitialisation(uid, token, password):
    """Change le mot de passe si le lien est valide ; renvoie True en cas de succès."""
    try:
        compte = CompteUtilisateur.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (CompteUtilisateur.DoesNotExist, ValueError, TypeError, OverflowError):
        return False
    if not default_token_generator.check_token(compte, token):
        return False
    compte.set_password(password)
    compte.save(update_fields=['password'])
    return True
