"""Mixins réutilisables des vues de comptes."""

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from . import protection_connexion

MESSAGE_BLOCAGE = (
    'Trop de tentatives de connexion. Réessayez dans {minutes} minutes.'
)


class LimitationTentativesConnexionMixin:
    """Bloque temporairement la connexion après trop d'échecs (e-mail ou IP).

    Tout refus de la vue parente compte comme un échec, qu'il soit levé
    (identifiants faux : 401 de simplejwt ; pro non validé : 400) ou
    renvoyé sous forme de réponse d'erreur.
    """

    def post(self, request, *args, **kwargs):
        email = str(request.data.get('email', ''))
        ip = protection_connexion.adresse_ip(request)

        if protection_connexion.est_bloque(email, ip):
            return Response(
                {'detail': MESSAGE_BLOCAGE.format(minutes=settings.CONNEXION_BLOCAGE_MINUTES)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            reponse = super().post(request, *args, **kwargs)
        except APIException:
            protection_connexion.enregistrer_echec(email, ip)
            raise
        if reponse.status_code == status.HTTP_200_OK:
            protection_connexion.reinitialiser(email)
        else:
            protection_connexion.enregistrer_echec(email, ip)
        return reponse
