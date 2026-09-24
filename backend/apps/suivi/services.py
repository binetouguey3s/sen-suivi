"""Logique métier de l'auto-évaluation (docs/SPECIFICATIONS.md section 2).

Isolée des vues et des sérialiseurs : une vue orchestre, elle ne calcule pas
(docs/CONTEXTE.md section 7, style de code back-end).
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


SEUIL_SUGGESTION_PROFESSIONNELS = 33  # au-dessus : niveau modéré ou élevé


def texte_interpretation(score):
    """Texte affiché sous la jauge (sans jamais parler de diagnostic)."""
    if score <= 33:
        return (
            "Vos réponses indiquent que vous traversez une période plutôt sereine. "
            "Continuez à prendre soin de vous : quelques minutes de respiration ou "
            "de marche chaque jour aident à garder cet équilibre."
        )
    if score <= 66:
        return (
            "Vos réponses indiquent que vous traversez actuellement une période de "
            "tensions qui impacte votre équilibre quotidien. Il est tout à fait normal "
            "de se sentir parfois dépassé face aux défis de la vie, et reconnaître ces "
            "signes est le premier pas vers un mieux-être. Prenez le temps d'écouter "
            "vos besoins et n'hésitez pas à solliciter un soutien bienveillant pour "
            "vous accompagner."
        )
    return (
        "Vos réponses indiquent une période particulièrement chargée. Vous n'êtes pas "
        "seul : échanger avec un professionnel peut vous soulager. Si vous avez besoin "
        "d'être écouté maintenant, le numéro vert d'écoute 800 805 805 est disponible."
    )


def suggerer_professionnels(utilisateur, score):
    """Jusqu'à 3 professionnels VALIDE ; aucun si le niveau est faible.

    Priorité aux professionnels de la ville de l'utilisateur (docs/SPECIFICATIONS.md
    section 2), puis aux autres.
    """
    if score <= SEUIL_SUGGESTION_PROFESSIONNELS:
        return []
    valides = list(Professionnel.objects.filter(statut_validation=StatutValidationPro.VALIDE))
    ville = (utilisateur.ville or '').strip().lower()
    if ville:
        valides.sort(key=lambda p: ville not in p.ville.lower())
    return valides[:3]
