"""Validation de la sortie du modèle de langage (niveau 2b).

Une réponse générée n'est montrée à l'utilisateur que si elle passe TOUTES
les règles ci-dessous. Au moindre écart, elle est rejetée et le chatbot
retombe sur la réponse de repli : mieux vaut une réponse sobre qu'une réponse
qui blesse, diagnostique ou invente.
"""

import re
import unicodedata
from dataclasses import dataclass

from app.config.regles_reponse import (
    CONSEILS_INTERDITS,
    EXHORTATIONS,
    FORMULES_CREUSES,
    MOTS_VIDES,
    NUMEROS_AUTORISES,
    PHRASES_MAX,
    PHRASES_MAX_ECOUTE,
    PROMESSES_INTERDITES,
    QUESTIONS_MAX,
    SIMILARITE_REPETITION_MAX,
    TERMES_CLINIQUES,
    TERMES_PAYANTS,
)


@dataclass
class ResultatValidation:
    valide: bool
    raison: str | None = None


def _normaliser(texte: str) -> str:
    """Minuscules, sans accents, apostrophes typographiques unifiées."""
    texte = texte.replace('’', "'").replace('ʼ', "'")
    sans_accents = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii')
    return sans_accents.lower()


def _motif(expression: str) -> re.Pattern:
    """Expression cherchée mot par mot ; « * » final = racine, sinon pluriel et féminin admis."""
    if expression.endswith('*'):
        return re.compile(r'(?<![a-z])' + re.escape(expression[:-1]))
    return re.compile(r'(?<![a-z])' + re.escape(expression) + r'(?:e?s)?(?![a-z])')


_MOTIFS = {
    nom: [(expr, _motif(expr)) for expr in liste]
    for nom, liste in {
        'formule creuse': FORMULES_CREUSES,
        'terme clinique': TERMES_CLINIQUES,
        'promesse interdite': PROMESSES_INTERDITES,
        'sujet payant': TERMES_PAYANTS,
        'conseil interdit': CONSEILS_INTERDITS,
    }.items()
}

# Exhortation : le mot ouvre une phrase, ou il est suivi d'un point d'exclamation
_EXHORTATIONS = [
    (mot, re.compile(r'(?:^|[.!?…]\s*)' + re.escape(mot) + r'(?![a-z])|(?<![a-z])' + re.escape(mot) + r'\s*!'))
    for mot in EXHORTATIONS
]

# Tutoiement : pronoms de la deuxième personne du singulier
_TUTOIEMENT = re.compile(r"(?<![a-z])(?:tu|toi|ton|ta|tes|te|t')(?![a-z])")
# Début de ligne en liste à puces ou numérotée
_LISTE = re.compile(r'^\s*(?:[-*•–]|\d+[.)])\s+', re.MULTILINE)
# Suite de chiffres, éventuellement séparés par des espaces, points ou tirets
_NUMERO = re.compile(r'\d[\d .-]*\d|\d')


# Fin de phrase attendue : ponctuation finale, éventuellement suivie d'un guillemet
_FIN_ACHEVEE = re.compile(r'[.!?…][\s»"”)]*$')


def reponse_achevee(texte: str) -> bool:
    """Vrai si la réponse se termine par une ponctuation finale.

    Certains modèles s'arrêtent au milieu d'une phrase en signalant pourtant
    une fin normale : « demander une » ne doit jamais être montré.
    """
    return bool(_FIN_ACHEVEE.search(texte.strip()))


def _compter_phrases(texte: str) -> int:
    morceaux = re.split(r'(?<=[.!?…])\s+', texte.strip())
    return len([m for m in morceaux if re.search(r'[a-zA-Z]', m)])


def mots_significatifs(texte: str) -> set[str]:
    """Racines des mots porteurs de sens (quatre lettres ou plus, hors mots vides).

    Les six premières lettres suffisent à rapprocher « inspirez » et « inspirer »,
    ou « ressource » et « ressources ».
    """
    return {mot[:6] for mot in re.findall(r'[a-z]+', _normaliser(texte)) if len(mot) >= 4 and mot not in MOTS_VIDES}


def _similarite(a: str, b: str) -> float:
    mots_a, mots_b = mots_significatifs(a), mots_significatifs(b)
    if not mots_a or not mots_b:
        return 0.0
    return len(mots_a & mots_b) / len(mots_a | mots_b)


def valider(
    reponse: str, ressources: list[dict], mode: str = 'ressources', precedentes: list[str] | None = None
) -> ResultatValidation:
    """Vérifie une réponse générée ; `ressources` = celles fournies au modèle.

    Mode « ressources » : une réponse sans ressource est toujours rejetée.
    Mode « écoute » : pas de ressource attendue, mais une réponse plus courte.
    `precedentes` : réponses déjà données par Titou dans la conversation.
    """
    if not reponse or not reponse.strip():
        return ResultatValidation(False, 'réponse vide')
    if not reponse_achevee(reponse):
        return ResultatValidation(False, 'réponse inachevée')
    if mode == 'ressources' and not ressources:
        return ResultatValidation(False, 'réponse générée sans ressource')
    phrases_max = PHRASES_MAX_ECOUTE if mode == 'ecoute' else PHRASES_MAX

    normalise = _normaliser(reponse)

    for nom, motifs in _MOTIFS.items():
        for expression, motif in motifs:
            if motif.search(normalise):
                return ResultatValidation(False, f'{nom} : « {expression.rstrip("*")} »')

    for mot, motif in _EXHORTATIONS:
        if motif.search(normalise):
            return ResultatValidation(False, f'formule creuse : « {mot} »')

    if _TUTOIEMENT.search(normalise):
        return ResultatValidation(False, 'tutoiement')
    if _LISTE.search(reponse):
        return ResultatValidation(False, 'liste à puces')
    if _compter_phrases(reponse) > phrases_max:
        return ResultatValidation(False, f'plus de {phrases_max} phrases')
    if reponse.count('?') > QUESTIONS_MAX:
        return ResultatValidation(False, 'plus d\'une question')

    for numero in _NUMERO.findall(reponse):
        chiffres = re.sub(r'\D', '', numero)
        # Les petits nombres (« 5 minutes », « 4 temps ») ne sont pas des numéros
        if len(chiffres) >= 4 and chiffres not in NUMEROS_AUTORISES:
            return ResultatValidation(False, f'numéro non autorisé : {numero.strip()}')

    for precedente in precedentes or []:
        if _similarite(reponse, precedente) > SIMILARITE_REPETITION_MAX:
            return ResultatValidation(False, 'répétition d\'une réponse précédente')

    return ResultatValidation(True)
