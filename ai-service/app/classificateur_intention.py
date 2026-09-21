"""Niveau 1 du chatbot : classification d'intention.

Approche par mots-clés pondérés plutôt que par modèle entraîné : le chatbot
ne répond qu'à partir de contenus validés (jamais de LLM génératif libre),
et une classification simple, déterministe et explicable convient mieux à
un projet évalué en certification qu'un modèle opaque.

Chaque intention reconnue avec confiance a une réponse validée prédéfinie.
Si aucune ne dépasse le seuil de confiance, on passe au RAG (niveau 2).
"""

import unicodedata
from dataclasses import dataclass

SEUIL_CONFIANCE_INTENTION = 0.70

# (expression, poids) : une expression explicite pèse plus qu'un simple mot.
_MOTS_CLES: dict[str, list[tuple[str, float]]] = {
    'STRESS': [
        ('je suis stresse', 0.8), ('je me sens stresse', 0.8), ('stress', 0.4),
        ('anxieux', 0.4), ('anxiete', 0.4), ('panique', 0.4), ('sous pression', 0.5),
        ('angoisse', 0.4), ('examen', 0.3), ('surmene', 0.4),
    ],
    'FATIGUE': [
        ('je suis fatigue', 0.8), ('je dors mal', 0.8), ('fatigue', 0.4),
        ('epuise', 0.5), ('epuisement', 0.5), ('insomnie', 0.6),
        ('n\'arrive pas a dormir', 0.7), ('mal a dormir', 0.6), ('sommeil', 0.3),
    ],
    'BESOIN_ECOUTE': [
        ('besoin de parler', 0.8), ('envie de parler', 0.7), ('personne a qui parler', 0.8),
        ('je me sens seul', 0.7), ('solitude', 0.5), ('je me sens seule', 0.7),
        ('triste', 0.4), ('besoin d\'ecoute', 0.8), ('me sens incompris', 0.6),
    ],
    'QUESTION_RESSOURCE': [
        ('je cherche un professionnel', 0.8), ('chercher un professionnel', 0.8),
        ('besoin d\'un professionnel', 0.8), ('recommandation', 0.4),
        ('une ressource', 0.5), ('un exercice', 0.4), ('un article', 0.4),
        ('ou trouver de l\'aide', 0.7), ('un psychologue', 0.6), ('un coach', 0.5),
    ],
    'URGENCE': [
        ('besoin d\'aide tout de suite', 0.8), ('c\'est urgent', 0.8),
        ('j\'ai besoin d\'aide maintenant', 0.8), ('immediat', 0.4),
    ],
}

REPONSE_PAR_INTENTION: dict[str, str] = {
    'STRESS': (
        "Le stress que vous décrivez est éprouvant, et c'est courant d'en ressentir "
        "avant une échéance importante. Respirer profondément quelques minutes ou "
        "faire une courte pause peut déjà aider. Voici une ressource qui pourrait "
        "vous accompagner."
    ),
    'FATIGUE': (
        "Le manque de sommeil pèse sur tout le reste. Essayez de garder des horaires "
        "de coucher réguliers et d'éviter les écrans juste avant de dormir. Voici une "
        "ressource sur le sujet."
    ),
    'BESOIN_ECOUTE': (
        "Je suis là pour vous écouter. Vous pouvez aussi échanger avec d'autres "
        "personnes sur le forum de Sen Suivi, ou demander une mise en relation avec "
        "un professionnel si vous le souhaitez."
    ),
    'QUESTION_RESSOURCE': (
        "Vous pouvez consulter l'annuaire des professionnels validés par Sen Suivi et "
        "leur envoyer une demande de mise en relation directement depuis leur profil."
    ),
    'URGENCE': (
        "Si vous avez besoin d'aide rapidement, le numéro vert 800 805 805 et le SAMU "
        "(1515) sont disponibles. Vous pouvez aussi demander une mise en relation avec "
        "un professionnel validé par Sen Suivi."
    ),
}

# Thématique de ressource suggérée pour chaque intention (utilisée par le RAG
# comme filtre de secours quand une intention est reconnue sans y être liée
# directement, ex. proposer un article après une réponse de niveau 1).
THEMATIQUE_PAR_INTENTION: dict[str, str] = {
    'STRESS': 'Stress',
    'FATIGUE': 'Sommeil',
}


@dataclass
class ResultatClassification:
    intention: str
    confiance: float

    @property
    def reconnue_avec_confiance(self) -> bool:
        return self.confiance >= SEUIL_CONFIANCE_INTENTION


def _normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii')
    return sans_accents.lower()


def classifier(message: str) -> ResultatClassification:
    """Renvoie l'intention la plus probable et son niveau de confiance (0 à 1)."""
    normalise = _normaliser(message)
    meilleure_intention = 'AUTRE'
    meilleur_score = 0.0

    for intention, expressions in _MOTS_CLES.items():
        score = sum(poids for expression, poids in expressions if _normaliser(expression) in normalise)
        score = min(score, 1.0)
        if score > meilleur_score:
            meilleur_score = score
            meilleure_intention = intention

    return ResultatClassification(intention=meilleure_intention, confiance=meilleur_score)
