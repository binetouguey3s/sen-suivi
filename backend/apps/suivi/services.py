"""Logique métier de l'auto-évaluation (docs/SPECIFICATIONS.md section 2).

Isolée des vues et des sérialiseurs : une vue orchestre, elle ne calcule pas
(CLAUDE.md section 7, style de code back-end).
"""

from apps.comptes.models import Professionnel, StatutValidationPro


def calculer_score_de_tendance(valeurs):
    """Score brut (0-32) ramené sur 100, arrondi à l'entier."""
    score_brut = sum(valeurs)
    return round((score_brut / 32) * 100)


def interpreter_score(score):
    """Libellé affiché associé à un score sur 100 (jamais de jauge rouge)."""
    if score <= 33:
        return 'Niveau faible'
    if score <= 66:
        return 'Niveau modéré'
    return 'Niveau élevé'


def suggerer_professionnels(utilisateur):
    """Jusqu'à 3 professionnels VALIDE, en priorité dans la ville de l'utilisateur.

    Utilisateur n'a pas de champ ville dans le modèle actuel : en son
    absence, la priorisation par ville n'est pas appliquée ici (voir la
    note remontée après l'exécution de ce plan). On se contente donc du
    filtre VALIDE, limité à 3.
    """
    return Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE)[:3]
