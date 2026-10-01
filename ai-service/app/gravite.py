"""Qualification d'une situation grave : risque vital, violences, ou détresse.

S'applique APRÈS le niveau 0 (detecteur_detresse.py, jamais modifié) : elle
ne remplace pas la détection, elle précise la nature de l'aide à apporter.
"""

import re
import unicodedata

from app.config.signaux_gravite import COMBINAISONS_DANGER, DANGER_AUTRUI, RISQUE_VITAL, VIOLENCES
from app.detecteur_detresse import detecter_detresse

REPONSE_VIOLENCES = (
    "Ce que vous vivez est grave, et vous n'y êtes pour rien. Vous avez le droit d'être protégé·e et "
    "accompagné·e. Si vous êtes en danger maintenant, appelez le 1515 (SAMU) ou le 18. Pour en parler à "
    "quelqu'un tout de suite, le numéro vert 800 805 805 est gratuit. Un psychologue ou un assistant "
    "social de Sen Suivi peut aussi vous accompagner, en toute confidentialité."
)


REPONSE_DANGER_AUTRUI = (
    "Ce que vous ressentez semble très fort en ce moment, et vous avez bien fait de l'écrire plutôt que "
    "de le garder pour vous. Si vous sentez que vous pourriez passer à l'acte, éloignez-vous tout de suite "
    "de la situation et de la personne, et appelez le 800 805 805 pour en parler, gratuitement. En cas de "
    "danger immédiat, appelez le 1515 (SAMU) ou le 18. Un psychologue de Sen Suivi peut aussi vous aider "
    "à traverser ce moment, en toute confidentialité."
)


def _normaliser(texte: str) -> str:
    """Minuscules, sans accents, lettres répétées réduites (« alummer », « allumer »
    et « allllumer » s'écrivent tous « alumer ») : les fautes de frappe d'une
    personne bouleversée ne doivent pas cacher un danger."""
    texte = unicodedata.normalize('NFKD', texte or '').encode('ascii', 'ignore').decode('ascii').lower()
    texte = re.sub(r'([a-z])\1+', r'\1', texte)
    return ' ' + re.sub(r"[^a-z]+", ' ', texte).strip() + ' '


def _motif(expression: str) -> str:
    racine = expression.endswith('*')
    expression = _normaliser(expression.rstrip('*')).strip()
    if racine:
        return r'(?<![a-z])' + re.escape(expression)
    return r'(?<![a-z])' + re.escape(expression) + r'(?![a-z])'


def _contient(normalise: str, expressions: list[str]) -> bool:
    return any(re.search(_motif(e), normalise) for e in expressions)


def violences(texte: str) -> bool:
    return _contient(_normaliser(texte), VIOLENCES)


def danger_autrui(texte: str) -> bool:
    normalise = _normaliser(texte)
    if _contient(normalise, DANGER_AUTRUI):
        return True
    mots = set(normalise.split())
    return any(_normaliser(cle).strip() in mots and mots & {_normaliser(m).strip() for m in avec}
               for cle, avec in COMBINAISONS_DANGER)


def nature_grave(texte: str) -> str | None:
    """Nature d'un message grave, dans l'ordre de priorité ; None sinon."""
    if detecter_detresse(texte):
        return 'RISQUE_VITAL' if risque_vital(texte) else 'DETRESSE'
    if danger_autrui(texte):
        return 'DANGER_AUTRUI'
    if violences(texte):
        return 'VIOLENCES'
    return None


def risque_vital(texte: str) -> bool:
    return _contient(_normaliser(texte), RISQUE_VITAL)
