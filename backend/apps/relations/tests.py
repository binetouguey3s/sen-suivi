"""Tests des demandes de mise en relation : notification du professionnel via n8n,
puis messagerie privée une fois la demande acceptée."""

from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.comptes.models import Professionnel, StatutValidationPro, Utilisateur
from apps.notifications.models import NotificationEmail

from .models import DemandeContact, MessageRelation


class NouvelleDemandeTests(APITestCase):
    def setUp(self):
        self.professionnel = Professionnel.objects.create(
            email='pro@test.sn', nom='Test Pro', specialite='PSYCHOLOGUE', ville='Dakar',
            langue='français', tarif_indicatif=10000, statut_validation=StatutValidationPro.VALIDE,
        )
        self.utilisateur = Utilisateur.objects.create(email='user@test.sn', nom='Diop', prenom='Awa')
        self.client.force_authenticate(self.utilisateur)

    @patch('apps.relations.views.declencher_workflow')
    def test_le_workflow_n8n_est_declenche_avec_le_seul_pseudonyme(self, declencher):
        reponse = self.client.post(
            '/api/demandes-contact', {'professionnel': self.professionnel.pk, 'message': 'Bonjour'}, format='json'
        )
        self.assertEqual(reponse.status_code, 201)
        declencher.assert_called_once_with(
            'nouvelle-demande',
            {'professionnel_id': self.professionnel.pk, 'pseudonyme': self.utilisateur.pseudonyme},
        )
        # Jamais l'identité de l'utilisateur avant l'acceptation
        donnees = declencher.call_args.args[1]
        self.assertNotIn('Awa', str(donnees))
        self.assertNotIn('user@test.sn', str(donnees))


class MessagerieTests(APITestCase):
    def setUp(self):
        self.pro = Professionnel.objects.create(
            email='pro@test.sn', nom='Sokhna Mbaye', specialite='SOPHROLOGUE', ville='Mbour',
            langue='français', tarif_indicatif=10000, statut_validation=StatutValidationPro.VALIDE,
            consultation_distance=True,
        )
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.demande = DemandeContact.objects.create(utilisateur=self.awa, professionnel=self.pro, message='Bonjour')
        self.url = f'/api/demandes-contact/{self.demande.pk}/messages'

    def ecrire(self, compte, contenu='Bonjour, merci d’avoir accepté.'):
        self.client.force_authenticate(compte)
        return self.client.post(self.url, {'contenu': contenu}, format='json')

    def test_la_conversation_ne_s_ouvre_qu_apres_l_acceptation(self):
        self.assertEqual(self.ecrire(self.awa).status_code, 403)
        self.demande.accepter()
        self.assertEqual(self.ecrire(self.awa).status_code, 201)

    def test_une_demande_declinee_n_ouvre_aucune_conversation(self):
        self.demande.refuser()
        self.assertEqual(self.ecrire(self.awa).status_code, 403)

    def test_personne_d_autre_ne_peut_lire_ni_ecrire(self):
        self.demande.accepter()
        self.ecrire(self.awa)
        intrus = Utilisateur.objects.create(email='intrus@test.sn', nom='X', prenom='Y')

        self.client.force_authenticate(intrus)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.ecrire(intrus).status_code, 404)

    def test_les_deux_personnes_echangent_et_les_messages_lus_sont_marques(self):
        self.demande.accepter()
        self.ecrire(self.awa, 'Bonjour')
        self.ecrire(self.pro, 'Bonjour Awa, quand êtes-vous disponible ?')

        self.client.force_authenticate(self.awa)
        liste = self.client.get('/api/demandes-contact').data
        self.assertEqual(liste[0]['non_lus'], 1)

        messages = self.client.get(self.url).data
        self.assertEqual([(m['contenu'], m['de_moi']) for m in messages],
                         [('Bonjour', True), ('Bonjour Awa, quand êtes-vous disponible ?', False)])
        self.assertEqual(self.client.get('/api/demandes-contact').data[0]['non_lus'], 0)

    def test_l_utilisateur_voit_les_modalites_du_professionnel(self):
        self.client.force_authenticate(self.awa)
        demande = self.client.get('/api/demandes-contact').data[0]
        self.assertEqual((demande['professionnel_specialite'], demande['consultation_distance']), ('Sophrologue', True))

    def test_la_notification_ne_contient_jamais_le_message_et_ne_se_repete_pas(self):
        self.demande.accepter()
        self.ecrire(self.awa, 'Je traverse un moment difficile au travail')
        self.ecrire(self.awa, 'Et je dors mal')

        notifications = NotificationEmail.objects.filter(destinataire=self.pro)
        self.assertEqual(notifications.count(), 1)
        self.assertNotIn('difficile', notifications.get().contenu)
        self.assertIn(self.awa.pseudonyme, notifications.get().contenu)

    def test_un_message_vide_est_refuse(self):
        self.demande.accepter()
        self.assertEqual(self.ecrire(self.awa, '   ').status_code, 400)
        self.assertFalse(MessageRelation.objects.exists())
