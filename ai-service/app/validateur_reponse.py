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
    METIERS,
    MOTS_DE_LIAISON,
    MOTS_REDITE_MIN,
    MOTS_ANGLAIS,
    MOTS_ANGLAIS_MAX,
    MOTS_VIDES,
    NUMEROS_AUTORISES,
    ORIENTATION,
    PHRASES_MAX,
    PHRASES_MAX_ECOUTE,
    PROMESSES_INTERDITES,
    QUESTIONS_MAX,
    RESOLUTIONS,
    SIMILARITE_REDITE_MAX,
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

_METIERS = {libelle: re.compile(r'(?<![a-z])(?:' + motif + ')') for libelle, motif in METIERS.items()}
_ORIENTATION = re.compile(ORIENTATION)

# Résolution d'une tâche hors du bien-être (calcul, code)
_RESOLUTIONS = [(nom, re.compile(motif, re.MULTILINE)) for nom, motif in RESOLUTIONS.items()]

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


def metiers_cites(texte: str) -> set[str]:
    """Métiers de l'annuaire nommés dans un texte (libellés de Django)."""
    normalise = _normaliser(texte)
    return {libelle for libelle, motif in _METIERS.items() if motif.search(normalise)}


def _mots(texte: str) -> list[str]:
    return re.findall(r'[a-z]+', _normaliser(texte))


def _redite(precedente: str, phrase: str) -> bool:
    """La phrase redit la précédente : identique, quasi identique, ou déjà contenue dedans."""
    avant, mots = _mots(precedente), _mots(phrase)
    if not mots or avant == mots:
        return bool(mots)
    coeur = [m for m in mots if m not in MOTS_DE_LIAISON]
    if len(coeur) >= MOTS_REDITE_MIN and f" {' '.join(coeur)} " in f" {' '.join(avant)} ":
        return True
    a, b = set(avant), set(mots)
    return min(len(a), len(b)) > MOTS_REDITE_MIN and len(a & b) / len(a | b) >= SIMILARITE_REDITE_MAX


def dedoublonner(texte: str) -> str:
    """Retire une phrase qui redit celle qui la précède, en gardant la première.

    Certains modèles bégaient : « … ce que beaucoup de personnes traversent.
    Beaucoup de personnes traversent cela. »
    """
    phrases = [p for p in re.split(r'(?<=[.!?…])\s+', texte.strip()) if p]
    gardees: list[str] = []
    for phrase in phrases:
        if gardees and _redite(gardees[-1], phrase):
            continue
        gardees.append(phrase)
    return ' '.join(gardees)


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
    reponse: str,
    ressources: list[dict],
    mode: str = 'ressources',
    precedentes: list[str] | None = None,
    controle_metier: bool = False,
    metier_attendu: str | None = None,
) -> ResultatValidation:
    """Vérifie une réponse générée ; `ressources` = celles fournies au modèle.

    Mode « ressources » : une réponse sans ressource est toujours rejetée.
    Mode « écoute » : pas de ressource attendue, mais une réponse plus courte.
    `precedentes` : réponses déjà données par Titou dans la conversation.
    `controle_metier` : une carte de professionnel peut s'afficher sous la
    réponse ; si elle oriente, elle ne nomme que `metier_attendu` (le métier de
    la carte), ou aucun métier quand personne n'est disponible.
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

    for nom, motif in _RESOLUTIONS:
        if motif.search(normalise):
            return ResultatValidation(False, f'résolution : {nom}')
    if sum(mot in MOTS_ANGLAIS for mot in re.findall(r'[a-z]+', normalise)) > MOTS_ANGLAIS_MAX:
        return ResultatValidation(False, 'résolution : texte en anglais')

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

    if controle_metier and _ORIENTATION.search(normalise):
        autres = metiers_cites(reponse) - ({metier_attendu} if metier_attendu else set())
        if autres:
            return ResultatValidation(False, f'métier différent de la suggestion : {", ".join(sorted(autres))}')

    for precedente in precedentes or []:
        if _similarite(reponse, precedente) > SIMILARITE_REPETITION_MAX:
            return ResultatValidation(False, 'répétition d\'une réponse précédente')

    return ResultatValidation(True)
