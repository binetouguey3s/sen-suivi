"""Tests de l'endpoint interne appelé par n8n pour créer une notification."""

from django.test import override_settings
from rest_framework.test import APITestCase

from apps.comptes.models import Professionnel, StatutValidationPro

from .models import NotificationEmail

CLE = 'cle-de-test'


@override_settings(N8N_API_KEY=CLE)
class CreerNotificationInterneTests(APITestCase):
    url = '/api/interne/notifications-email'

    def setUp(self):
        self.professionnel = Professionnel.objects.create(
            email='pro@test.sn', nom='Test Pro', specialite='PSYCHOLOGUE', ville='Dakar',
            langue='français', tarif_indicatif=10000, statut_validation=StatutValidationPro.VALIDE,
        )

    def envoyer(self, **extra):
        corps = {'destinataire_id': self.professionnel.pk, 'objet': 'Objet', 'contenu': 'Contenu', **extra}
        return self.client.post(self.url, corps, format='json', headers={'X-Cle-Interne': CLE})

    def test_notification_creee_par_defaut(self):
        reponse = self.envoyer(preference='nouvelle_demande')
        self.assertEqual(reponse.status_code, 201)
        self.assertEqual(NotificationEmail.objects.filter(destinataire=self.professionnel).count(), 1)

    def test_preference_desactivee_respectee(self):
        self.professionnel.preferences = {'nouvelle_demande': {'email': False, 'push': True}}
        self.professionnel.save()
        reponse = self.envoyer(preference='nouvelle_demande')
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.data['ignoree'])
        self.assertFalse(NotificationEmail.objects.filter(destinataire=self.professionnel).exists())

    def test_cle_interne_obligatoire(self):
        reponse = self.client.post(self.url, {'destinataire_id': self.professionnel.pk, 'objet': 'o', 'contenu': 'c'}, format='json')
        # Sans clé ni jeton, la requête est non authentifiée (401)
        self.assertEqual(reponse.status_code, 401)
        self.assertFalse(NotificationEmail.objects.exists())
