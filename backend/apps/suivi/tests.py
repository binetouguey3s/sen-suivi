"""Test exigé : calcul du score de tendance."""

from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.chatbot.models import ConversationChatbot, MessageChatbot
from apps.comptes.models import Utilisateur
from apps.ressources.models import Ressource

from .models import AutoEvaluation, OptionReponse, QuestionEvaluation, SuiviHumeur, TypeEvaluation
from .profil_tendance import ELEMENTS_MAX, LONGUEUR_MAX, profil_tendance
from .services import calculer_score_de_tendance, interpreter_score

URL_AUTO_EVALUATIONS = '/api/auto-evaluations'


class ScoreDeTendanceTests(SimpleTestCase):
    def test_score_minimal(self):
        self.assertEqual(calculer_score_de_tendance([0] * 8), 0)

    def test_score_maximal(self):
        self.assertEqual(calculer_score_de_tendance([4] * 8), 100)

    def test_score_intermediaire_arrondi_a_l_entier(self):
        # 8 réponses de valeur 1 = 8 sur 32 = 25 sur 100
        self.assertEqual(calculer_score_de_tendance([1] * 8), 25)
        # 13 sur 32 = 40,625 -> 41
        self.assertEqual(calculer_score_de_tendance([2, 2, 2, 2, 2, 1, 1, 1]), 41)

    def test_interpretation_par_seuils(self):
        self.assertEqual(interpreter_score(25), 'Niveau faible')
        self.assertEqual(interpreter_score(50), 'Niveau modéré')
        self.assertEqual(interpreter_score(80), 'Niveau élevé')

    def test_le_maximum_suit_les_questions_reellement_posees(self):
        # 9 questions notées de 0 à 4 : 18 sur 36 = 50, et non 18 sur 32 = 56
        self.assertEqual(calculer_score_de_tendance([2] * 9, [4] * 9), 50)
        # Une question notée de 0 à 3 : 3 sur 3 compte pour 100 %
        self.assertEqual(calculer_score_de_tendance([4] * 7 + [3], [4] * 7 + [3]), 100)

    def test_sans_maximum_le_score_vaut_zero(self):
        self.assertEqual(calculer_score_de_tendance([], []), 0)


class EnvoiAutoEvaluationTests(APITestCase):
    """Le pourcentage renvoyé correspond exactement aux réponses données."""

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.client.force_authenticate(self.utilisateur)
        self.questions = []
        for ordre in range(1, 9):
            question = QuestionEvaluation.objects.create(
                type_evaluation=TypeEvaluation.STRESS, libelle=f'Question {ordre}', ordre=ordre
            )
            for valeur, libelle in enumerate(['Jamais', 'Rarement', 'Parfois', 'Souvent', 'Presque tout le temps']):
                OptionReponse.objects.create(question=question, libelle=libelle, valeur=valeur)
            self.questions.append(question)

    def _reponses(self, valeurs):
        return [
            {'question': q.id, 'option': q.options.get(valeur=v).id} for q, v in zip(self.questions, valeurs)
        ]

    def test_le_score_renvoye_est_le_pourcentage_exact(self):
        reponse = self.client.post(
            URL_AUTO_EVALUATIONS,
            {'type_evaluation': 'STRESS', 'reponses': self._reponses([2, 2, 2, 2, 2, 1, 1, 1])},
            format='json',
        )

        self.assertEqual(reponse.status_code, 201)
        self.assertEqual(reponse.data['score_de_tendance'], 41)
        self.assertEqual(reponse.data['interpretation'], 'Niveau modéré')

    def test_une_question_repondue_deux_fois_est_refusee(self):
        reponses = self._reponses([4] * 8) + self._reponses([4])

        reponse = self.client.post(
            URL_AUTO_EVALUATIONS, {'type_evaluation': 'STRESS', 'reponses': reponses}, format='json'
        )

        self.assertEqual(reponse.status_code, 400)
        self.assertFalse(AutoEvaluation.objects.exists())


class NoteDuJournalTests(APITestCase):
    """La note du journal accepte 1 000 caractères (limite de l'interface)."""

    def test_une_note_de_1000_caracteres_est_enregistree_en_entier(self):
        utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.client.force_authenticate(utilisateur)
        note = 'Aujourd’hui, ce qui m’a fait du bien ' + 'x' * 963

        reponse = self.client.post('/api/suivi-humeur', {'score_humeur': 'BIEN', 'note': note, 'etiquettes': ''}, format='json')

        self.assertEqual(reponse.status_code, 201, reponse.data)
        self.assertEqual(len(note), 1000)
        self.assertEqual(SuiviHumeur.objects.get(utilisateur=utilisateur).note, note)


class ProfilTendanceTests(APITestCase):
    """Résumé anonyme : quelques mots-clés, jamais de donnée brute."""

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.aujourd_hui = timezone.localdate()

    def _journal(self, humeurs, depuis=0):
        """Une entrée par jour, la dernière il y a `depuis` jours."""
        for decalage, humeur in enumerate(reversed(humeurs)):
            SuiviHumeur.objects.create(
                utilisateur=self.utilisateur,
                date=self.aujourd_hui - timedelta(days=depuis + decalage),
                score_humeur=humeur,
                note='Texte privé du journal',
            )

    def test_une_humeur_qui_baisse_est_resumee_en_mots_cles(self):
        self._journal(['BIEN', 'BIEN', 'BIEN', 'MAL', 'MAL', 'TRES_MAL'])

        profil = profil_tendance(self.utilisateur)

        self.assertIn('humeur en baisse sur 7 jours', profil)
        self.assertIn('journal irrégulier', profil)
        self.assertNotIn('Texte privé du journal', ' '.join(profil))

    def test_une_humeur_qui_remonte(self):
        self._journal(['MAL', 'MAL', 'NEUTRE', 'BIEN', 'TRES_BIEN'])
        self.assertIn('humeur en hausse sur 7 jours', profil_tendance(self.utilisateur))

    def test_une_humeur_stable(self):
        self._journal(['NEUTRE', 'BIEN', 'NEUTRE', 'BIEN'])
        self.assertIn('humeur stable sur 7 jours', profil_tendance(self.utilisateur))

    def test_trop_peu_d_entrees_pour_parler_de_tendance(self):
        self._journal(['MAL', 'BIEN'])
        self.assertFalse(any(e.startswith('humeur') for e in profil_tendance(self.utilisateur)))

    def test_l_article_s_elide_devant_une_voyelle(self):
        AutoEvaluation.objects.create(utilisateur=self.utilisateur, type_evaluation='ANXIETE', score_de_tendance=80)
        self.assertIn("niveau d'inquiétude élevé au dernier test", profil_tendance(self.utilisateur))

    def test_un_journal_quotidien(self):
        self._journal(['NEUTRE'] * 12)
        self.assertIn('journal quotidien', profil_tendance(self.utilisateur))

    def test_un_journal_arrete_depuis_plusieurs_jours(self):
        self._journal(['NEUTRE', 'NEUTRE'], depuis=6)
        self.assertIn('journal arrêté depuis 6 jours', profil_tendance(self.utilisateur))

    def test_le_dernier_test_resume_les_niveaux_moderes_ou_eleves(self):
        AutoEvaluation.objects.create(utilisateur=self.utilisateur, type_evaluation='FATIGUE', score_de_tendance=75)
        AutoEvaluation.objects.create(utilisateur=self.utilisateur, type_evaluation='STRESS', score_de_tendance=20)

        profil = profil_tendance(self.utilisateur)

        self.assertIn('niveau de fatigue élevé au dernier test', profil)
        self.assertFalse(any('stress' in e for e in profil))
        self.assertIn("dernier test aujourd'hui", profil)

    def test_seul_le_resultat_le_plus_recent_de_chaque_type_compte(self):
        ancien = AutoEvaluation.objects.create(utilisateur=self.utilisateur, type_evaluation='STRESS', score_de_tendance=80)
        AutoEvaluation.objects.filter(pk=ancien.pk).update(date=timezone.now() - timedelta(days=40))
        AutoEvaluation.objects.create(utilisateur=self.utilisateur, type_evaluation='STRESS', score_de_tendance=50)

        self.assertIn('niveau de stress modéré au dernier test', profil_tendance(self.utilisateur))

    def test_les_themes_frequents_viennent_des_ressources_evoquees(self):
        conversation = ConversationChatbot.objects.create(utilisateur=self.utilisateur, consentement_conservation=True)
        sommeil = Ressource.objects.create(titre='Dormir mieux', type_ressource='ARTICLE', contenu='…', thematique='Sommeil')
        for _ in range(2):
            MessageChatbot.objects.create(conversation=conversation, contenu='…', type_expediteur='BOT', ressource=sommeil)

        self.assertIn('thèmes fréquents : sommeil', profil_tendance(self.utilisateur))

    def test_sans_aucune_donnee_le_profil_est_vide(self):
        self.assertEqual(profil_tendance(self.utilisateur), [])


ONBOARDING_COMPLET = {
    'version': 1, 'statut': 'termine', 'date': '2026-10-01T10:00:00Z',
    'genre': 'femme', 'tranche_age': '18-24', 'situation': 'etudiant', 'langue': 'fr',
    'humeur': 2, 'energie': 30, 'sommeil': 'difficile',
    'preoccupations': ['stress', 'sommeil'], 'rien_de_particulier': False,
    'bien_etre': ['musique', 'respiration', 'spiritualite'], 'spiritualite': ['coran', 'dhikr'],
    'moments': ['soir'], 'duree': '5-10', 'formats': ['audio'], 'rappels': True, 'frequence_rappels': '3_semaine',
    'echange_pro': 'plus_tard', 'metiers': ['SOPHROLOGUE'], 'aise_avec': 'femme',
}


class ProfilOnboardingTests(APITestCase):
    """Ce que la personne a dit dans l'onboarding, en mots-clés : jamais de donnée brute."""

    def setUp(self):
        self.utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')

    def _avec(self, onboarding):
        self.utilisateur.preferences = {'personnalisation_chatbot': True, 'onboarding': onboarding}
        self.utilisateur.save()
        return profil_tendance(self.utilisateur)

    def test_un_onboarding_complet_donne_des_libelles(self):
        self.assertEqual(self._avec(ONBOARDING_COMPLET), [
            'préoccupations : stress, sommeil',
            'ce qui fait du bien : musique, respiration, spiritualité et prière',
            'moment préféré : le soir',
            'format préféré : audio',
            'durée : 5-10 min',
            'situation : étudiant·e',
            'langue : français',
            'souhaite échanger avec un professionnel : plus tard',
            "métiers qui l'intéressent : sophrologue",
        ])

    def test_jamais_genre_age_spiritualite_detaillee_humeur_ni_aisance(self):
        texte = ' '.join(self._avec(ONBOARDING_COMPLET)).lower()
        for interdit in ('femme', '18', 'coran', 'dhikr', 'énergie', 'humeur', 'difficile', 'aise'):
            self.assertNotIn(interdit, texte)

    def test_un_onboarding_passe_partiel_ne_donne_que_les_champs_remplis(self):
        profil = self._avec({'statut': 'passe', 'preoccupations': ['etudes'], 'bien_etre': [], 'metiers': []})
        self.assertEqual(profil, ['préoccupations : études et examens'])

    def test_rien_de_particulier(self):
        profil = self._avec({'statut': 'termine', 'preoccupations': [], 'rien_de_particulier': True})
        self.assertEqual(profil, ['préoccupations : rien de particulier'])

    def test_pas_de_metiers_si_la_personne_ne_veut_pas_de_professionnel(self):
        profil = self._avec({'statut': 'termine', 'echange_pro': 'pas_maintenant', 'metiers': ['PSYCHOLOGUE']})
        self.assertEqual(profil, ["souhaite échanger avec un professionnel : pas pour l’instant"])

    def test_sans_onboarding_rien_n_est_ajoute(self):
        self.utilisateur.preferences = {'personnalisation_chatbot': True}
        self.utilisateur.save()
        self.assertEqual(profil_tendance(self.utilisateur), [])

    def test_des_codes_inconnus_sont_ignores(self):
        self.assertEqual(self._avec({'preoccupations': ['inconnu', 7], 'moments': 'soir'}), ['moment préféré : le soir'])

    def test_les_limites_du_microservice_sont_respectees(self):
        # Journal et tests chargés, onboarding complet : jamais plus de 10 éléments de 80 caractères
        for decalage in range(12):
            SuiviHumeur.objects.create(utilisateur=self.utilisateur, date=timezone.localdate() - timedelta(days=decalage),
                                       score_humeur='BIEN' if decalage > 6 else 'MAL')
        for type_evaluation in ('STRESS', 'ANXIETE', 'FATIGUE'):
            AutoEvaluation.objects.create(utilisateur=self.utilisateur, type_evaluation=type_evaluation, score_de_tendance=80)
        onboarding = {**ONBOARDING_COMPLET, 'metiers': list(
            ['PSYCHOLOGUE', 'ASSISTANT_SOCIAL', 'COACH_DEVELOPPEMENT', 'SOPHROLOGUE', 'MEDIATEUR_FAMILIAL', 'COACH_SPORTIF']
        )}

        profil = self._avec(onboarding)

        self.assertLessEqual(len(profil), ELEMENTS_MAX)
        self.assertTrue(all(len(e) <= LONGUEUR_MAX for e in profil))
        # La tendance du journal passe d'abord, l'onboarding garde sa place
        self.assertTrue(profil[0].startswith('humeur'))
        self.assertIn('préoccupations : stress, sommeil', profil)
