"""Cadrage du chatbot : détection des demandes hors du bien-être.

Exécuté juste après le niveau 0 (détresse, danger pour autrui, violences, qui
restent toujours prioritaires) et avant la classification d'intention. Une
demande de tâche ou d'information sans lien avec le bien-être (calcul, devoir,
code, traduction, actualité, recette, conseil médical…) reçoit un recadrage
prédéfini, sans appel au modèle de langage.

Un signal de bien-être ou une mention de la plateforme l'emporte toujours :
« j'ai un examen de maths demain et je panique » reste dans le cadre.
"""

import re
import unicodedata

from app.config.hors_sujet import (
    MENTIONS_PLATEFORME,
    MOTIFS_HORS_SUJET,
    OPERATIONS_CHIFFREES,
    REPONSES_RECADRAGE,
    SIGNAUX_BIEN_ETRE,
)


def _normaliser(texte: str) -> str:
    """Minuscules, sans accents, apostrophes unifiées, traits d'union remplacés par des espaces."""
    texte = texte.replace('’', "'").replace('ʼ', "'").replace('-', ' ')
    sans_accents = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', sans_accents.lower())


def _motif(expression: str) -> re.Pattern:
    """Expression cherchée mot par mot ; « * » final = racine, sinon pluriel et féminin admis."""
    expression = _normaliser(expression)
    if expression.endswith('*'):
        return re.compile(r'(?<![a-z])' + re.escape(expression[:-1]))
    return re.compile(r'(?<![a-z])' + re.escape(expression) + r'(?:e?s)?(?![a-z])')


_SIGNAUX = [_motif(e) for e in SIGNAUX_BIEN_ETRE + MENTIONS_PLATEFORME]
_MOTIFS = {categorie: [_motif(e) for e in liste] for categorie, liste in MOTIFS_HORS_SUJET.items()}
_OPERATIONS = [re.compile(motif) for motif in OPERATIONS_CHIFFREES]


def dans_le_cadre(message: str) -> bool:
    """Vrai si le message exprime un ressenti ou parle de la plateforme."""
    normalise = _normaliser(message)
    return any(motif.search(normalise) for motif in _SIGNAUX)


def detecter_hors_sujet(message: str) -> str | None:
    """Catégorie de la demande hors sujet (CALCUL_DEVOIRS, TACHE…), ou None."""
    if dans_le_cadre(message):
        return None
    normalise = _normaliser(message)
    # Opérations cherchées sans remplacer les tirets : « 2x-3=7 »
    if any(motif.search(message.lower()) for motif in _OPERATIONS):
        return 'CALCUL_DEVOIRS'
    for categorie, motifs in _MOTIFS.items():
        if any(motif.search(normalise) for motif in motifs):
            return categorie
    return None


def reponse_recadrage(categorie: str, precedentes: list[str] | None = None) -> str:
    """Recadrage de la catégorie : une variante pas encore envoyée, sinon une
    autre que le dernier message de Titou. Jamais deux fois de suite le même."""
    variantes = REPONSES_RECADRAGE[categorie]
    precedentes = precedentes or []
    dernier = precedentes[-1] if precedentes else None
    return next((v for v in variantes if v not in precedentes), next(v for v in variantes if v != dernier))
