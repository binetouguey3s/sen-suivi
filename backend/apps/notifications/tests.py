"""Tests de l'endpoint interne appelé par n8n pour créer une notification."""

from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comptes.models import Professionnel, StatutValidationPro, Utilisateur
from apps.suivi.models import AutoEvaluation, SuiviHumeur

from .interne import OBJET_RAPPEL, OBJET_RAPPEL_TEST
from .models import NotificationEmail
from .services import notifier

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


@override_settings(N8N_API_KEY=CLE, RAPPEL_JOURNAL_JOURS=3, RAPPEL_TEST_JOURS=30, RAPPEL_FREQUENCE_MAX_JOURS=7)
class RappelsTests(APITestCase):
    """Rappels doux : réglages lus depuis le .env, désactivables, jamais répétés."""

    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        Utilisateur.objects.filter(pk=self.awa.pk).update(date_creation=timezone.now() - timedelta(days=60))
        self.awa.refresh_from_db()

    def lire(self, url):
        return self.client.get(url, headers={'X-Cle-Interne': CLE}).data

    def inactifs(self):
        return self.lire('/api/interne/utilisateurs-inactifs')

    def a_retester(self):
        return self.lire('/api/interne/utilisateurs-a-retester')

    def test_un_journal_vide_depuis_plusieurs_jours_declenche_un_rappel_doux(self):
        rappel, = self.inactifs()
        self.assertEqual((rappel['id'], rappel['preference']), (self.awa.pk, 'rappel_journal'))
        self.assertIn('si vous en avez envie', rappel['contenu'])
        self.assertTrue(rappel['contenu'].startswith('Bonjour Awa'))

    def test_un_journal_recent_ne_declenche_rien(self):
        SuiviHumeur.objects.create(utilisateur=self.awa, date=timezone.localdate(), score_humeur='BIEN')
        self.assertEqual(self.inactifs(), [])

    def test_le_rappel_desactive_dans_les_parametres_est_respecte(self):
        self.awa.preferences = {'rappel_journal': {'email': False, 'push': True}}
        self.awa.save()
        self.assertEqual(self.inactifs(), [])

    def test_jamais_plus_d_un_rappel_pendant_la_frequence_maximale(self):
        notifier(self.awa, OBJET_RAPPEL_TEST, 'Faire le point')
        self.assertEqual(self.inactifs(), [])

    def test_une_fois_la_frequence_passee_le_rappel_peut_revenir(self):
        ancien = notifier(self.awa, OBJET_RAPPEL, 'Rappel')
        NotificationEmail.objects.filter(pk=ancien.pk).update(date_envoi=timezone.now() - timedelta(days=8))
        self.assertEqual(len(self.inactifs()), 1)

    def test_un_test_de_plus_d_un_mois_propose_de_le_refaire(self):
        SuiviHumeur.objects.create(utilisateur=self.awa, date=timezone.localdate(), score_humeur='BIEN')
        test = AutoEvaluation.objects.create(utilisateur=self.awa, type_evaluation='STRESS', score_de_tendance=40)
        AutoEvaluation.objects.filter(pk=test.pk).update(date=timezone.now() - timedelta(days=35))

        rappel, = self.a_retester()

        self.assertEqual((rappel['id'], rappel['preference']), (self.awa.pk, 'rappel_auto_evaluation'))

    def test_un_test_recent_ou_absent_ne_declenche_rien(self):
        self.assertEqual(self.a_retester(), [])
        AutoEvaluation.objects.create(utilisateur=self.awa, type_evaluation='STRESS', score_de_tendance=40)
        self.assertEqual(self.a_retester(), [])
