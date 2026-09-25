"""Tests des demandes de mise en relation : notification du professionnel via n8n."""

from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.comptes.models import Professionnel, StatutValidationPro, Utilisateur


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
