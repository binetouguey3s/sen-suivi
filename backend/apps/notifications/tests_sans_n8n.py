"""Hébergement sans n8n (N8N_WEBHOOK_URL vide) : Django fait lui-même l'essentiel."""

from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.comptes.models import Administrateur, Professionnel, StatutValidationPro

from .models import NotificationEmail
from .services import declencher_workflow


@override_settings(N8N_WEBHOOK_URL='', EMAIL_NOTIFICATIONS=False)
class SansN8nTests(TestCase):
    @patch('apps.notifications.services.httpx.post')
    def test_le_professionnel_est_prevenu_d_une_nouvelle_demande(self, post):
        pro = Professionnel.objects.create(
            email='pro@test.sn', nom='Test Pro', specialite='PSYCHOLOGUE', ville='Dakar',
            langue='français', tarif_indicatif=10000, statut_validation=StatutValidationPro.VALIDE,
        )
        declencher_workflow('nouvelle-demande', {'professionnel_id': pro.pk, 'pseudonyme': 'Baobab-12'})

        notification = NotificationEmail.objects.get(destinataire=pro)
        self.assertEqual(notification.objet, 'Nouvelle demande de mise en relation')
        self.assertIn('Baobab-12', notification.contenu)
        post.assert_not_called()

    def test_les_administrateurs_sont_prevenus_d_une_inscription(self):
        Administrateur.objects.create(email='admin@test.sn', nom='Admin')
        declencher_workflow('nouveau-professionnel', {'nom': 'Awa Ndiaye', 'specialite': 'Sophrologue', 'ville': 'Thiès'})

        notification = NotificationEmail.objects.get()
        self.assertEqual(notification.objet, 'Nouvelle inscription professionnelle à valider')
        self.assertIn('Awa Ndiaye (Sophrologue, Thiès)', notification.contenu)

    @patch('apps.ressources.indexation.reindexer_rag')
    def test_une_ressource_modifiee_relance_l_indexation(self, reindexer):
        with patch('apps.notifications.services.threading.Thread') as fil:
            declencher_workflow('ressource-modifiee')
        fil.return_value.start.assert_called_once()


class SanteTests(TestCase):
    def test_l_adresse_de_sante_repond(self):
        reponse = self.client.get('/api/sante')
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.json(), {'statut': 'ok'})


class DomainesSansEnvoiTests(TestCase):
    @override_settings(EMAIL_DOMAINES_SANS_ENVOI=['sensuivi.sn'])
    @patch('apps.notifications.courriel.send_mail')
    def test_aucun_email_vers_les_comptes_de_demonstration(self, send_mail):
        from .courriel import envoyer

        self.assertFalse(envoyer('awa.ndiaye@sensuivi.sn', 'Rappel', 'Bonjour'))
        send_mail.assert_not_called()
        self.assertTrue(envoyer('vraie.personne@gmail.com', 'Rappel', 'Bonjour'))
        send_mail.assert_called_once()
