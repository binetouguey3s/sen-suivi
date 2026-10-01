"""Volet E : orientation vers le bon professionnel et accès à la mise en relation."""

from datetime import timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comptes.models import Professionnel, StatutValidationPro, Utilisateur
from apps.relations.models import DemandeContact
from apps.suivi.models import AutoEvaluation

from .acces import etat_acces
from .models import AccesMiseEnRelation, MoyenPaiement, StatutAcces
from .services import besoins_de, classer, suggerer
from .urgence import emettre_jeton

AUJOURD_HUI = timezone.localdate()
HIER = (AUJOURD_HUI - timedelta(days=1)).isoformat()
DANS_43_JOURS = (AUJOURD_HUI + timedelta(days=42)).isoformat()


def professionnel(nom, specialite, ville='Dakar', langue='français', domaines=None, **extra):
    return Professionnel.objects.create(
        email=f'{nom.lower().replace(" ", ".")}@test.sn', nom=nom, specialite=specialite, ville=ville,
        langue=langue, tarif_indicatif=10000, statut_validation=StatutValidationPro.VALIDE,
        domaines=domaines or [], **extra,
    )


class AlgorithmeOrientationTests(APITestCase):
    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa', ville='Dakar')
        self.psy = professionnel('Fatou Sarr', 'PSYCHOLOGUE')
        self.sophro = professionnel('Moussa Ba', 'SOPHROLOGUE', domaines=['Sommeil', 'Respiration'])
        self.sportif = professionnel('Aliou Fall', 'COACH_SPORTIF', ville='Thiès', domaines=['Confiance en soi'])
        self.mediateur = professionnel('Aïda Ndiaye', 'MEDIATEUR_FAMILIAL', domaines=['Famille'])

    # Test 21
    def test_un_score_eleve_en_fatigue_propose_les_metiers_du_sommeil(self):
        AutoEvaluation.objects.create(utilisateur=self.awa, type_evaluation='FATIGUE', score_de_tendance=80)

        suggestion = suggerer(self.awa)

        self.assertIn(suggestion.professionnel.specialite, ['COACH_SPORTIF', 'SOPHROLOGUE'])
        self.assertEqual(suggestion.besoins, ['FATIGUE'])
        self.assertIn('le sommeil et la fatigue', suggestion.raison)

    def test_ce_que_dit_la_personne_passe_avant_ses_tests(self):
        AutoEvaluation.objects.create(utilisateur=self.awa, type_evaluation='FATIGUE', score_de_tendance=80)
        self.assertEqual(besoins_de(self.awa, ['Des disputes avec ma famille'])[:2], ['FAMILLE', 'FATIGUE'])

    def test_la_raison_explique_le_choix(self):
        suggestion = suggerer(self.awa, textes=['je dors mal'])
        self.assertEqual(suggestion.professionnel, self.sophro)
        self.assertEqual(
            suggestion.raison, 'Sophrologue, Moussa Ba accompagne le sommeil et la fatigue et consulte à Dakar.'
        )

    def test_la_langue_commune_departage_a_adequation_egale(self):
        wolof = professionnel('Ndeye Diallo', 'PSYCHOLOGUE', langue='français, wolof')
        suggestion = suggerer(self.awa, textes=['Dama sonn lool, xel bi dafa diis'], besoins=['DEUIL'])
        self.assertEqual(suggestion.professionnel, wolof)
        self.assertIn('parle wolof', suggestion.raison)

    def test_la_proximite_departage_a_adequation_et_langue_egales(self):
        thies = professionnel('Codou Faye', 'SOPHROLOGUE', ville='Thiès', domaines=['Sommeil', 'Respiration'])
        self.assertEqual(suggerer(self.awa, besoins=['FATIGUE'], ville='Thiès').professionnel, thies)

    def test_un_professionnel_indisponible_n_est_jamais_mis_en_avant(self):
        self.sophro.accepte_demandes = False
        self.sophro.save()
        self.assertNotEqual(suggerer(self.awa, textes=['je dors mal']).professionnel, self.sophro)

    def test_equite_le_moins_sollicite_passe_devant_a_egalite(self):
        jumeau = professionnel('Ousmane Sy', 'SOPHROLOGUE', domaines=['Sommeil', 'Respiration'])
        for _ in range(3):
            DemandeContact.objects.create(utilisateur=self.awa, professionnel=self.sophro)
        self.assertEqual(suggerer(self.awa, besoins=['FATIGUE']).professionnel, jumeau)

    def test_le_classement_est_reproductible(self):
        premier = [s.professionnel.pk for s in classer(['STRESS', 'FAMILLE'])]
        self.assertEqual(premier, [s.professionnel.pk for s in classer(['STRESS', 'FAMILLE'])])

    # Test 22
    def test_la_liste_complete_reste_accessible_malgre_la_suggestion(self):
        self.client.force_authenticate(self.awa)

        corps = self.client.get('/api/orientation/suggestion').data

        self.assertIsNotNone(corps['suggestion'])
        ids = {p['id'] for p in corps['professionnels']}
        self.assertEqual(ids, {self.psy.pk, self.sophro.pk, self.sportif.pk, self.mediateur.pk})


@override_settings(OFFRE_MODE='globale', ACCES_TARIF_FCFA=2000, ACCES_DUREE_JOURS=30, URGENCE_JETON_HEURES=24)
class AccesMiseEnRelationTests(APITestCase):
    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.pro = professionnel('Fatou Sarr', 'PSYCHOLOGUE')
        self.client.force_authenticate(self.awa)

    def demander(self, **entetes):
        return self.client.post(
            '/api/demandes-contact', {'professionnel': self.pro.pk, 'message': 'Bonjour'}, format='json',
            headers=entetes,
        )

    # Test 23
    @override_settings(OFFRE_DATE_FIN=DANS_43_JOURS)
    def test_pendant_l_offre_la_demande_aboutit_sans_paiement(self):
        etat = self.client.get('/api/acces/etat').data
        self.assertEqual((etat['offre_active'], etat['jours_restants'], etat['verrouille']), (True, 43, False))
        self.assertIsNone(etat['tarif_fcfa'])

        self.assertEqual(self.demander().status_code, 201)

    # Test 24
    @override_settings(OFFRE_DATE_FIN=HIER)
    def test_apres_l_offre_la_demande_declenche_l_ecran_de_deblocage(self):
        reponse = self.demander()

        self.assertEqual(reponse.status_code, 402)
        self.assertEqual(reponse.data['detail'].code, 'acces_verrouille')
        self.assertFalse(DemandeContact.objects.exists())
        etat = self.client.get('/api/acces/etat').data
        self.assertTrue(etat['verrouille'])
        self.assertEqual(etat['tarif_fcfa'], 2000)

    @override_settings(OFFRE_DATE_FIN=HIER)
    def test_un_acces_actif_debloque_la_mise_en_relation(self):
        AccesMiseEnRelation.objects.create(
            utilisateur=self.awa, moyen=MoyenPaiement.OFFERT, statut=StatutAcces.ACTIF,
            date_fin=AUJOURD_HUI + timedelta(days=10),
        )
        self.assertEqual(self.demander().status_code, 201)

    @override_settings(OFFRE_MODE='individuelle', OFFRE_DUREE_JOURS=60)
    def test_offre_individuelle_de_60_jours_a_partir_de_l_inscription(self):
        Utilisateur.objects.filter(pk=self.awa.pk).update(date_creation=timezone.now() - timedelta(days=59))
        self.awa.refresh_from_db()
        self.assertEqual(etat_acces(self.awa)['jours_restants'], 1)
        Utilisateur.objects.filter(pk=self.awa.pk).update(date_creation=timezone.now() - timedelta(days=60))
        self.awa.refresh_from_db()
        self.assertTrue(etat_acces(self.awa)['verrouille'])

    # Test 25
    @override_settings(OFFRE_DATE_FIN=HIER)
    @patch('apps.chatbot.views.traiter_message')
    def test_tout_le_reste_reste_gratuit_apres_l_offre(self, traiter):
        traiter.return_value = {'reponse': 'Bonjour.', 'source_reponse': 'REGLE', 'urgence': False,
                                'intention': None, 'ressource': None}
        acces_libres = [
            ('post', '/api/chatbot/message', {'message': 'Bonjour'}),
            ('get', '/api/suivi-humeur', None),
            ('get', '/api/auto-evaluations/questions/STRESS', None),
            ('get', '/api/ressources', None),
            ('get', '/api/lieux', None),
            ('get', '/api/forum/publications', None),
            ('get', '/api/professionnels/valides', None),
            ('get', f'/api/professionnels/{self.pro.pk}', None),
            ('get', '/api/orientation/suggestion', None),
        ]
        for methode, url, corps in acces_libres:
            with self.subTest(url=url):
                reponse = getattr(self.client, methode)(url, corps, format='json')
                self.assertNotIn(reponse.status_code, (402, 403, 404), url)

    # Test 26
    @override_settings(OFFRE_DATE_FIN=HIER)
    def test_en_detresse_ni_compteur_ni_paiement(self):
        jeton = emettre_jeton(self.awa)

        etat = self.client.get('/api/acces/etat', headers={'X-Jeton-Urgence': jeton}).data
        self.assertEqual(
            (etat['urgence'], etat['verrouille'], etat['jours_restants'], etat['tarif_fcfa']), (True, False, None, None)
        )
        self.assertEqual(self.demander(**{'X-Jeton-Urgence': jeton}).status_code, 201)

    @override_settings(OFFRE_DATE_FIN=HIER)
    def test_un_jeton_d_urgence_est_lie_au_compte_qui_l_a_recu(self):
        autre = Utilisateur.objects.create(email='fanta@test.sn', nom='Sow', prenom='Fanta')
        self.assertEqual(self.demander(**{'X-Jeton-Urgence': emettre_jeton(autre)}).status_code, 402)
        self.assertEqual(self.demander(**{'X-Jeton-Urgence': 'jeton-invente'}).status_code, 402)

    @override_settings(OFFRE_DATE_FIN=HIER)
    def test_le_paiement_n_a_encore_aucun_prestataire(self):
        reponse = self.client.post('/api/acces/paiement', {'moyen': 'WAVE', 'telephone': '77 123 45 67'}, format='json')
        self.assertEqual(reponse.status_code, 503)
        self.assertFalse(AccesMiseEnRelation.objects.exists())

    def test_un_professionnel_indisponible_ne_recoit_pas_de_demande(self):
        self.pro.accepte_demandes = False
        self.pro.save()
        self.assertEqual(self.demander().status_code, 400)


@patch('apps.chatbot.views.traiter_message')
class ChatbotOrientationTests(APITestCase):
    def setUp(self):
        self.awa = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa', ville='Dakar')
        self.sophro = professionnel('Moussa Ba', 'SOPHROLOGUE', domaines=['Gestion du stress'])
        self.client.force_authenticate(self.awa)

    def reponse_ia(self, **extra):
        return {'reponse': 'Réponse.', 'source_reponse': 'GENERATION', 'urgence': False, 'intention': None,
                'ressource': None, 'orientation_professionnel': False, **extra}

    def test_une_demande_de_specialiste_affiche_le_professionnel_suggere(self, traiter):
        traiter.return_value = self.reponse_ia(orientation_professionnel=True)

        corps = self.client.post('/api/chatbot/message', {'message': 'Je veux un spécialiste pour mon stress'}).data

        self.assertEqual(corps['professionnel_suggere']['id'], self.sophro.pk)
        self.assertIn('le stress et la tension', corps['professionnel_suggere']['raison'])

    def test_le_microservice_sait_qu_une_suggestion_peut_s_afficher(self, traiter):
        traiter.return_value = self.reponse_ia()
        self.client.post('/api/chatbot/message', {'message': 'Bonjour'})
        self.assertTrue(traiter.call_args.args[3])

        self.client.force_authenticate(None)
        self.client.post('/api/chatbot/message', {'message': 'Bonjour'})
        self.assertFalse(traiter.call_args.args[3])

    def test_une_detresse_remet_un_jeton_et_propose_aussi_un_professionnel(self, traiter):
        psychologue = professionnel('Fatou Sarr', 'PSYCHOLOGUE')
        traiter.return_value = self.reponse_ia(urgence=True, nature_detresse='DETRESSE')

        corps = self.client.post('/api/chatbot/message', {'message': '…'}).data

        self.assertTrue(corps['jeton_urgence'])
        # Mise en relation gratuite avec le métier adapté, en plus des numéros
        self.assertEqual(corps['professionnel_suggere']['id'], psychologue.pk)

    def test_des_violences_orientent_vers_psychologue_ou_assistant_social(self, traiter):
        social = professionnel('Awa Sy', 'ASSISTANT_SOCIAL')
        traiter.return_value = self.reponse_ia(urgence=True, nature_detresse='VIOLENCES')

        corps = self.client.post('/api/chatbot/message', {'message': '…'}).data

        self.assertEqual(corps['professionnel_suggere']['id'], social.pk)
        self.assertIn('les violences subies', corps['professionnel_suggere']['raison'])
