"""Modération du forum côté Django : application des décisions, file des
administrateurs, contestation et compteur d'infractions.

Le microservice IA est remplacé par une doublure (aucun appel réel)."""

from unittest.mock import patch

import httpx
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.comptes.models import Administrateur, Utilisateur
from apps.notifications.models import NotificationEmail

from .moderation import infractions
from .models import ModerationMessage, PublicationForum, StatutModeration


def decision_ia(decision, categorie='CONFORME', gravite=1, message='', priorite=0, extrait=''):
    def faux_post(url, json, timeout):
        corps = {
            'decision': decision, 'categorie': categorie, 'gravite': gravite, 'extrait': extrait,
            'raison': 'raison de test', 'message': message, 'niveau': 'MODELE', 'priorite': priorite,
        }
        return httpx.Response(200, json=corps, request=httpx.Request('POST', url))

    return patch('apps.forum.moderation.httpx.post', side_effect=faux_post)


@override_settings(MODERATION_ASYNCHRONE=False, MODERATION_SEUIL_INFRACTIONS=2, MODERATION_SUSPENSION_JOURS=7)
class ModerationForumTests(APITestCase):
    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.admin = Administrateur.objects.create(email='admin@test.sn', nom='Admin')
        self.client.force_authenticate(self.awa)

    def publier(self, contenu='Un message pour le forum de Sen Suivi.'):
        with self.captureOnCommitCallbacks(execute=True):
            reponse = self.client.post(
                '/api/forum/publications', {'titre': 'Titre', 'contenu': contenu, 'thematique': 'STRESS'}, format='json'
            )
        self.assertEqual(reponse.status_code, 201)
        return PublicationForum.objects.get(pk=reponse.data['id'])

    def test_un_message_conforme_est_publie(self):
        with decision_ia('PUBLIER'):
            publication = self.publier()
        self.assertEqual(publication.statut_moderation, StatutModeration.VISIBLE)

    def test_le_message_est_en_attente_tant_que_la_decision_n_est_pas_prise(self):
        reponse = self.client.post(
            '/api/forum/publications', {'titre': 'T', 'contenu': 'Contenu', 'thematique': 'STRESS'}, format='json'
        )
        self.assertEqual(reponse.data['statut_moderation'], StatutModeration.EN_ATTENTE)

    def test_la_detresse_est_publiee_accompagnee_et_signalee(self):
        with decision_ia('PUBLIER_ACCOMPAGNER', 'DETRESSE', 3, message='Le 800 805 805 répond à toute heure.', priorite=2):
            publication = self.publier('Je ne vois plus de raison de continuer.')

        self.assertEqual(publication.statut_moderation, StatutModeration.VISIBLE)
        self.assertIn('800 805 805', NotificationEmail.objects.get(destinataire=self.awa).contenu)
        self.assertTrue(ModerationMessage.objects.get().a_traiter)

    def test_un_blocage_explique_ce_qui_pose_probleme(self):
        with decision_ia('BLOQUER', 'INSULTE', 2, message="Votre message n'a pas été publié… reformuler"):
            publication = self.publier()

        self.assertEqual(publication.statut_moderation, StatutModeration.BLOQUE)
        mes = self.client.get('/api/forum/mes-messages').data['messages'][0]
        self.assertEqual((mes['statut_moderation'], mes['peut_contester']), ('BLOQUE', True))
        self.assertIn('reformuler', mes['message'])

    # Test 14 (côté Django)
    def test_microservice_indisponible_le_message_attend_un_humain(self):
        with patch('apps.forum.moderation.httpx.post', side_effect=httpx.ConnectError('panne')):
            publication = self.publier()

        self.assertEqual(publication.statut_moderation, StatutModeration.EN_ATTENTE)
        self.assertTrue(ModerationMessage.objects.get().a_traiter)

    # Test 15
    def test_un_message_de_detresse_ne_compte_jamais_comme_infraction(self):
        with decision_ia('PUBLIER_ACCOMPAGNER', 'DETRESSE', 3, priorite=2):
            for _ in range(3):
                self.publier('Je ne vois plus de raison de continuer.')
        self.assertEqual(infractions(self.awa), 0)
        self.awa.refresh_from_db()
        self.assertIsNone(self.awa.forum_suspendu_jusqu_au)

    def test_au_dela_du_seuil_le_forum_est_suspendu(self):
        with decision_ia('BLOQUER', 'INSULTE', 2):
            self.publier('Premier message blessant')
            self.publier('Second message blessant')

        self.awa.refresh_from_db()
        self.assertIsNotNone(self.awa.forum_suspendu_jusqu_au)
        reponse = self.client.post(
            '/api/forum/publications', {'titre': 'T', 'contenu': 'Encore', 'thematique': 'STRESS'}, format='json'
        )
        self.assertEqual(reponse.status_code, 403)

    def test_l_auteur_peut_contester_et_l_admin_infirmer_en_un_clic(self):
        with decision_ia('BLOQUER', 'INSULTE', 2):
            publication = self.publier()

        reponse = self.client.post(
            f'/api/forum/mes-messages/publication/{publication.pk}/contester', {'motif': 'Je parlais de moi.'}, format='json'
        )
        self.assertEqual(reponse.status_code, 201)

        self.client.force_authenticate(self.admin)
        file = self.client.get('/api/forum/moderation/file').data
        self.assertEqual(file[0]['motif_contestation'], 'Je parlais de moi.')
        self.client.post(f"/api/forum/moderation/file/{file[0]['id']}", {'action': 'PUBLIER'}, format='json')

        publication.refresh_from_db()
        self.assertEqual(publication.statut_moderation, StatutModeration.VISIBLE)
        self.assertTrue(ModerationMessage.objects.get().infirmee)
        self.assertEqual(infractions(self.awa), 0)
        self.assertEqual(self.client.get('/api/forum/moderation/file').data, [])

    def test_une_decision_infirmee_leve_la_suspension(self):
        with decision_ia('BLOQUER', 'INSULTE', 2):
            premiere = self.publier('Premier')
            self.publier('Second')
        self.client.force_authenticate(self.admin)

        self.client.patch(f'/api/forum/moderation/publications/{premiere.pk}', {'statut_moderation': 'VISIBLE'}, format='json')

        self.awa.refresh_from_db()
        self.assertIsNone(self.awa.forum_suspendu_jusqu_au)

    def test_une_contestation_ne_peut_viser_qu_un_message_bloque(self):
        with decision_ia('PUBLIER'):
            publication = self.publier()
        reponse = self.client.post(f'/api/forum/mes-messages/publication/{publication.pk}/contester', {}, format='json')
        self.assertEqual(reponse.status_code, 403)

    def test_l_admin_voit_la_decision_de_l_ia_dans_ses_listes(self):
        with decision_ia('BLOQUER_PRIORITAIRE', 'HARCELEMENT', 3, extrait='je vais te frapper', priorite=2):
            self.publier()
        self.client.force_authenticate(self.admin)

        publication = self.client.get('/api/forum/moderation/publications').data[0]

        self.assertEqual(publication['decision_ia']['categorie'], 'HARCELEMENT')
        self.assertEqual(publication['decision_ia']['extrait'], 'je vais te frapper')
        statistiques = self.client.get('/api/forum/moderation/statistiques').data
        self.assertEqual((statistiques['total'], statistiques['taux_blocage']), (1, 100))

    def test_le_spam_est_bloque_sans_notification(self):
        with decision_ia('BLOQUER_SILENCIEUX', 'SPAM'):
            publication = self.publier('Code promo sur www.boutique.sn')
        self.assertEqual(publication.statut_moderation, StatutModeration.BLOQUE)
        self.assertFalse(NotificationEmail.objects.exists())
