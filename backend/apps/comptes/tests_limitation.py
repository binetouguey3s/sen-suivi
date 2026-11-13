"""Limitation des envois par visiteur (config/limitation.py)."""

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework.test import APITestCase

from config.limitation import LimiteEcritures

PLAFONDS_BAS = {
    **settings.REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {'chatbot': '2/min', 'inscription': '2/min', 'reinitialisation': '2/min', 'forum': '2/min'},
}


@override_settings(REST_FRAMEWORK=PLAFONDS_BAS)
class LimitationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_au_dela_du_plafond_les_envois_sont_refuses(self):
        for _ in range(2):
            reponse = self.client.post('/api/auth/mot-de-passe-oublie', {'email': 'x@test.sn'})
            self.assertEqual(reponse.status_code, 200)
        reponse = self.client.post('/api/auth/mot-de-passe-oublie', {'email': 'x@test.sn'})
        self.assertEqual(reponse.status_code, 429)

    def test_la_lecture_n_est_jamais_comptee(self):
        limite, vue = LimiteEcritures(), type('Vue', (), {'throttle_scope': 'forum'})()
        lecture = type('Requete', (), {'method': 'GET'})()
        self.assertTrue(all(limite.allow_request(lecture, vue) for _ in range(10)))
