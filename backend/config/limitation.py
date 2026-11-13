"""Limitation du nombre d'envois par visiteur (protection contre les abus).

Seules les écritures (POST, PUT, PATCH, DELETE) sont comptées : lire une page
n'est jamais limité. Les plafonds sont dans REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
(settings.py) et réglables par variables d'environnement.
"""

from rest_framework.permissions import SAFE_METHODS
from rest_framework.settings import api_settings
from rest_framework.throttling import ScopedRateThrottle


class LimiteEcritures(ScopedRateThrottle):
    def allow_request(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)

    def get_rate(self):
        # Relu à chaque requête (DRF le fige au démarrage) : les plafonds
        # suivent ainsi les réglages, y compris ceux modifiés par les tests
        return api_settings.DEFAULT_THROTTLE_RATES.get(self.scope)
