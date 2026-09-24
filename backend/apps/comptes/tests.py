"""Tests des comptes.

- Test exigé : refus de connexion d'un
  professionnel non validé (route POST /api/auth/login).
- Directive de sécurité : robustesse des mots de passe et protection
  contre la force brute.
"""

from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings
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


# ---------------------------------------------------------------------
# Directive de sécurité : robustesse des mots de passe (section 2A)
# ---------------------------------------------------------------------


class RobustesseMotDePasseTests(SimpleTestCase):
    def refuse(self, mot_de_passe):
        with self.assertRaises(ValidationError, msg=mot_de_passe):
            validate_password(mot_de_passe)

    def test_trop_court(self):
        self.refuse('Ab1!xyz')

    def test_moins_de_trois_categories(self):
        self.refuse('dakarsenegal')   # minuscules seules
        self.refuse('dakarsenegal7')  # minuscules + chiffres

    def test_mot_de_passe_compromis_connu(self):
        self.refuse('Password1')

    def test_suites_evidentes(self):
        self.refuse('Teranga12345!')
        self.refuse('Azerty!Ngor7')
        self.refuse('Baobab!98765')
        self.refuse('Qwerty#Sine4')

    def test_caractere_repete(self):
        self.refuse('Jammmm!2026')

    def test_mots_de_passe_acceptes(self):
        for mot_de_passe in ('MotDePasse2026!', 'Teranga#Ngor7', 'baobab-du-sine-26', 'Liberty2026!'):
            validate_password(mot_de_passe)


class InscriptionMotDePasseFaibleTests(APITestCase):
    def test_inscription_refusee_avec_message_sur_le_mot_de_passe(self):
        reponse = self.client.post('/api/auth/register', {
            'nom': 'Diop', 'prenom': 'Awa', 'email': 'awa@test.sn', 'password': 'azerty123',
        })
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('password', reponse.data)
        self.assertFalse(Utilisateur.objects.filter(email='awa@test.sn').exists())


# ---------------------------------------------------------------------
# Directive de sécurité : protection contre la force brute (section 2C)
# ---------------------------------------------------------------------

@override_settings(CONNEXION_TENTATIVES_MAX=5, CONNEXION_BLOCAGE_MINUTES=15)
class ForceBruteConnexionTests(APITestCase):
    url = '/api/auth/login'

    def setUp(self):
        cache.clear()
        self.utilisateur = Utilisateur.objects.create(email='fatou@test.sn', nom='Ndiaye', prenom='Fatou')
        self.utilisateur.set_password(MOT_DE_PASSE)
        self.utilisateur.save()

    def connecter(self, email='fatou@test.sn', mot_de_passe=MOT_DE_PASSE, ip='10.0.0.1'):
        return self.client.post(self.url, {'email': email, 'password': mot_de_passe}, REMOTE_ADDR=ip)

    def test_blocage_du_compte_apres_cinq_echecs(self):
        for _ in range(5):
            self.assertEqual(self.connecter(mot_de_passe='Mauvais#2026').status_code, 401)
        # 6e tentative, même avec le bon mot de passe et depuis une autre IP : bloquée.
        reponse = self.connecter(ip='10.0.0.2')
        self.assertEqual(reponse.status_code, 429)
        self.assertNotIn('access', reponse.data)
        self.assertIn('15 minutes', reponse.data['detail'])

    def test_blocage_de_l_ip_apres_cinq_echecs_sur_des_comptes_differents(self):
        for i in range(5):
            self.connecter(email=f'inconnu{i}@test.sn')
        # L'IP est bloquée, même pour un compte jamais visé.
        self.assertEqual(self.connecter().status_code, 429)
        # Depuis une autre IP, le compte reste accessible.
        self.assertEqual(self.connecter(ip='10.0.0.9').status_code, 200)

    def test_quatre_echecs_ne_bloquent_pas(self):
        for _ in range(4):
            self.connecter(mot_de_passe='Mauvais#2026')
        self.assertEqual(self.connecter().status_code, 200)

    def test_succes_remet_le_compteur_du_compte_a_zero(self):
        for _ in range(4):
            self.connecter(mot_de_passe='Mauvais#2026', ip='10.0.0.3')
        self.assertEqual(self.connecter(ip='10.0.0.4').status_code, 200)
        for _ in range(4):
            self.connecter(mot_de_passe='Mauvais#2026', ip='10.0.0.5')
        self.assertEqual(self.connecter(ip='10.0.0.6').status_code, 200)

    def test_en_tete_x_forwarded_for_ignore(self):
        for i in range(5):
            self.client.post(
                self.url,
                {'email': f'inconnu{i}@test.sn', 'password': 'x'},
                REMOTE_ADDR='10.0.0.7',
                HTTP_X_FORWARDED_FOR=f'192.168.1.{i}',
            )
        self.assertEqual(self.connecter(ip='10.0.0.7').status_code, 429)
