"""Test exigé : calcul du score de tendance."""

from django.test import SimpleTestCase

from .services import calculer_score_de_tendance, interpreter_score


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
