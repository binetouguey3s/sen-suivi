"""Test exigé : refus de connexion d'un
professionnel non validé (route POST /api/auth/login)."""

from rest_framework.test import APITestCase

from .models import Professionnel, StatutValidationPro, Utilisateur

MOT_DE_PASSE = 'MotDePasse2026!'


def creer_professionnel(statut, email):
    professionnel = Professionnel.objects.create(
        email=email,
        nom='Test Pro',
        specialite='PSYCHOLOGUE',
        ville='Dakar',
        langue='français',
        tarif_indicatif=10000,
        statut_validation=statut,
    )
    professionnel.set_password(MOT_DE_PASSE)
    professionnel.save()
    return professionnel


class ConnexionProfessionnelTests(APITestCase):
    url = '/api/auth/login'

    def test_professionnel_en_attente_refuse(self):
        creer_professionnel(StatutValidationPro.EN_ATTENTE, 'attente@test.sn')
        reponse = self.client.post(self.url, {'email': 'attente@test.sn', 'password': MOT_DE_PASSE})
        self.assertEqual(reponse.status_code, 400)
        self.assertNotIn('access', reponse.data)

    def test_professionnel_refuse_ne_peut_pas_se_connecter(self):
        creer_professionnel(StatutValidationPro.REFUSE, 'refuse@test.sn')
        reponse = self.client.post(self.url, {'email': 'refuse@test.sn', 'password': MOT_DE_PASSE})
        self.assertEqual(reponse.status_code, 400)
        self.assertNotIn('access', reponse.data)

    def test_professionnel_valide_peut_se_connecter(self):
        creer_professionnel(StatutValidationPro.VALIDE, 'valide@test.sn')
        reponse = self.client.post(self.url, {'email': 'valide@test.sn', 'password': MOT_DE_PASSE})
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('access', reponse.data)

    def test_utilisateur_n_est_pas_concerne_par_la_validation(self):
        utilisateur = Utilisateur.objects.create(email='user@test.sn', nom='Test', prenom='User')
        utilisateur.set_password(MOT_DE_PASSE)
        utilisateur.save()
        reponse = self.client.post(self.url, {'email': 'user@test.sn', 'password': MOT_DE_PASSE})
        self.assertEqual(reponse.status_code, 200)
