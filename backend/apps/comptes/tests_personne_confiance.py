"""Personne de confiance : prévenue seulement à la demande de l'utilisateur,
en situation de détresse, et sans jamais le contenu des échanges."""

from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.orientation.urgence import emettre_jeton

from .models import AlerteConfiance, PersonneConfiance, Utilisateur

URL = '/api/comptes/moi/personne-confiance'
FATOU = {'prenom': 'Fatou', 'lien': 'Sœur', 'telephone': '77 123 45 67', 'email': 'fatou@test.sn', 'accord_confirme': True}


class PersonneConfianceTests(APITestCase):
    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.client.force_authenticate(self.awa)

    def enregistrer(self, **changements):
        return self.client.put(URL, {**FATOU, **changements}, format='json')

    def alerter(self, canal, jeton=True):
        entetes = {'X-Jeton-Urgence': emettre_jeton(self.awa)} if jeton else {}
        return self.client.post(f'{URL}/alerte', {'canal': canal}, format='json', headers=entetes)

    def test_aucune_personne_de_confiance_par_defaut(self):
        self.assertIsNone(self.client.get(URL).data)

    def test_l_accord_de_la_personne_est_obligatoire(self):
        self.assertEqual(self.enregistrer(accord_confirme=False).status_code, 400)
        self.assertFalse(PersonneConfiance.objects.exists())

    def test_il_faut_au_moins_un_moyen_de_la_joindre(self):
        self.assertEqual(self.enregistrer(telephone='', email='').status_code, 400)

    def test_le_message_propose_ne_contient_que_l_essentiel(self):
        corps = self.enregistrer().data

        self.assertEqual((corps['prenom'], corps['telephone']), ('Fatou', '771234567'))
        self.assertIn('Awa', corps['message_sms'])
        self.assertIn('1515', corps['message_sms'])

    def test_on_peut_la_retirer_a_tout_moment(self):
        self.enregistrer()
        self.client.delete(URL)
        self.assertFalse(PersonneConfiance.objects.exists())

    def test_l_alerte_n_existe_qu_en_situation_de_detresse(self):
        self.enregistrer()
        self.assertEqual(self.alerter('SMS', jeton=False).status_code, 403)

    def test_un_appel_ou_un_sms_part_du_telephone_de_l_utilisateur(self):
        self.enregistrer()
        with patch('apps.comptes.personne_confiance.declencher_workflow') as declencher:
            self.assertEqual(self.alerter('SMS').status_code, 201)
        declencher.assert_not_called()
        self.assertEqual(AlerteConfiance.objects.get().canal, 'SMS')

    @patch('apps.comptes.personne_confiance.declencher_workflow')
    def test_l_e_mail_ne_contient_jamais_le_contenu_des_echanges(self, declencher):
        self.enregistrer()

        self.alerter('EMAIL')

        nom, donnees = declencher.call_args.args
        self.assertEqual((nom, donnees['destinataire_email']), ('alerte-personne-confiance', 'fatou@test.sn'))
        self.assertNotIn('suicid', str(donnees).lower())
        self.assertNotIn('awa@test.sn', str(donnees))

    @patch('apps.comptes.personne_confiance.declencher_workflow')
    def test_la_personne_n_est_jamais_submergee_d_e_mails(self, declencher):
        self.enregistrer()
        self.alerter('EMAIL')
        self.alerter('EMAIL')
        self.assertEqual(declencher.call_count, 1)

    def test_le_jeton_d_un_autre_compte_ne_suffit_pas(self):
        self.enregistrer()
        autre = Utilisateur.objects.create(email='x@test.sn', nom='X', prenom='Y')
        reponse = self.client.post(
            f'{URL}/alerte', {'canal': 'SMS'}, format='json', headers={'X-Jeton-Urgence': emettre_jeton(autre)}
        )
        self.assertEqual(reponse.status_code, 403)
