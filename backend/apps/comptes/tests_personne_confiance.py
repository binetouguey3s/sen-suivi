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
        with patch('apps.comptes.personne_confiance.envoyer', return_value=True) as envoyer:
            self.assertEqual(self.alerter('SMS').status_code, 201)
        envoyer.assert_not_called()
        self.assertEqual(AlerteConfiance.objects.get().canal, 'SMS')

    @patch('apps.comptes.personne_confiance.envoyer', return_value=True)
    def test_l_e_mail_ne_contient_jamais_le_contenu_des_echanges(self, envoyer):
        self.enregistrer()

        self.assertEqual(self.alerter('EMAIL').status_code, 201)

        adresse, objet, contenu = envoyer.call_args.args
        self.assertEqual(adresse, 'fatou@test.sn')
        self.assertIn('Awa', objet)
        self.assertNotIn('suicid', contenu.lower())
        self.assertNotIn('awa@test.sn', contenu)

    @patch('apps.comptes.personne_confiance.envoyer', return_value=True)
    def test_la_personne_n_est_jamais_submergee_d_e_mails(self, envoyer):
        self.enregistrer()
        self.alerter('EMAIL')
        self.alerter('EMAIL')
        self.assertEqual(envoyer.call_count, 1)

    @patch('apps.comptes.personne_confiance.envoyer', return_value=False)
    def test_un_e_mail_qui_ne_part_pas_le_dit_et_propose_l_appel(self, envoyer):
        self.enregistrer()
        reponse = self.alerter('EMAIL')
        self.assertEqual(reponse.status_code, 502)
        self.assertIn('Appelez', reponse.data['detail'])

    def test_le_jeton_d_un_autre_compte_ne_suffit_pas(self):
        self.enregistrer()
        autre = Utilisateur.objects.create(email='x@test.sn', nom='X', prenom='Y')
        reponse = self.client.post(
            f'{URL}/alerte', {'canal': 'SMS'}, format='json', headers={'X-Jeton-Urgence': emettre_jeton(autre)}
        )
        self.assertEqual(reponse.status_code, 403)


@patch('apps.chatbot.views.traiter_message')
@patch('apps.notifications.courriel.envoyer', return_value=True)
class AlerteAutomatiqueTests(APITestCase):
    """Risque vital : la personne de confiance est prévenue automatiquement,
    seulement si l'utilisateur l'a accepté à l'avance, et jamais pour des violences."""

    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.client.force_authenticate(self.awa)
        self.client.put(URL, {**FATOU, 'alerte_automatique': True}, format='json')

    def ecrire(self, traiter, nature, message='…'):
        traiter.return_value = {'reponse': 'Réponse d’urgence.', 'source_reponse': 'REGLE', 'urgence': True,
                                'intention': None, 'ressource': None, 'nature_detresse': nature}
        with self.settings(EMAIL_ASYNCHRONE=False):
            return self.client.post('/api/chatbot/message', {'message': message}).data

    def test_un_risque_vital_previent_la_personne_avec_des_conseils_pour_bien_parler(self, envoyer, traiter):
        corps = self.ecrire(traiter, 'RISQUE_VITAL')

        self.assertEqual(corps['personne_confiance_prevenue'], 'Fatou')
        adresse, objet, contenu = envoyer.call_args.args
        self.assertEqual(adresse, 'fatou@test.sn')
        self.assertTrue(objet.startswith('Urgence'))
        # La raison est expliquée, sans jamais citer les messages
        self.assertIn('sa vie pourrait être en danger', contenu)
        self.assertIn("a accepté, à l'avance", contenu)
        self.assertIn('Écoutez sans juger', contenu)
        self.assertIn('800 805 805', contenu)
        self.assertNotIn('suicid', contenu.lower())

    def test_jamais_d_alerte_automatique_pour_des_violences(self, envoyer, traiter):
        corps = self.ecrire(traiter, 'VIOLENCES')
        self.assertIsNone(corps.get('personne_confiance_prevenue'))
        envoyer.assert_not_called()

    def test_un_danger_pour_autrui_previent_la_personne_avec_la_raison(self, envoyer, traiter):
        corps = self.ecrire(traiter, 'DANGER_AUTRUI', "j'ai envie de tuer mon mari")

        self.assertEqual(corps['personne_confiance_prevenue'], 'Fatou')
        contenu = envoyer.call_args.args[2]
        self.assertIn('passage à l\'acte dangereux', contenu)
        self.assertIn('Ne vous mettez pas vous-même en danger', contenu)
        self.assertNotIn('mari', contenu)

    def test_jamais_d_alerte_si_le_message_vise_la_personne_de_confiance(self, envoyer, traiter):
        # FATOU est « Sœur » : un message qui parle de la sœur ne la prévient pas
        for message in ["j'ai envie de tuer ma soeur", 'je vais faire du mal à Fatou']:
            self.assertIsNone(self.ecrire(traiter, 'DANGER_AUTRUI', message).get('personne_confiance_prevenue'))
        envoyer.assert_not_called()

    def test_toute_situation_grave_est_signalee_a_l_equipe_sans_le_contenu(self, envoyer, traiter):
        from apps.chatbot.models import SignalementRisque
        from apps.comptes.models import Administrateur
        from apps.notifications.models import NotificationEmail

        admin = Administrateur.objects.create(email='admin@test.sn', nom='Admin')

        self.ecrire(traiter, 'VIOLENCES', 'mon oncle me frappe')

        signalement = SignalementRisque.objects.get()
        self.assertEqual((signalement.nature, signalement.personne_confiance_prevenue), ('VIOLENCES', False))
        notification = NotificationEmail.objects.get(destinataire=admin)
        self.assertIn(self.awa.pseudonyme, notification.contenu)
        self.assertNotIn('oncle', notification.contenu)
        self.assertNotIn('Awa', notification.contenu)

    def test_sans_accord_prealable_rien_n_est_envoye(self, envoyer, traiter):
        self.client.put(URL, {**FATOU, 'alerte_automatique': False}, format='json')
        self.assertIsNone(self.ecrire(traiter, 'RISQUE_VITAL').get('personne_confiance_prevenue'))
        envoyer.assert_not_called()

    def test_une_seule_alerte_automatique_par_periode(self, envoyer, traiter):
        self.ecrire(traiter, 'RISQUE_VITAL')
        self.ecrire(traiter, 'RISQUE_VITAL')
        self.assertEqual(envoyer.call_count, 1)

    def test_l_alerte_automatique_demande_une_adresse_e_mail(self, envoyer, traiter):
        reponse = self.client.put(URL, {**FATOU, 'email': '', 'alerte_automatique': True}, format='json')
        self.assertEqual(reponse.status_code, 400)
