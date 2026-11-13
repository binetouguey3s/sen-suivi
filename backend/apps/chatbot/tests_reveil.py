"""Réveil du microservice IA à l'ouverture du site."""

from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APITestCase


class ReveilTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_le_reveil_repond_tout_de_suite_et_ne_part_qu_une_fois(self):
        with patch('threading.Thread') as fil:
            for _ in range(3):
                self.assertEqual(self.client.get('/api/chatbot/reveil').status_code, 204)
        fil.return_value.start.assert_called_once()
