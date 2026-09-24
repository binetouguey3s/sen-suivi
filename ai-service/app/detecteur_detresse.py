"""Niveau 0 du chatbot : détection de détresse (docs/CONTEXTE.md section 2).

Toujours exécuté en premier, avant la classification d'intention et le RAG.
Si un signal de détresse est détecté, la réponse est immédiatement les
ressources d'urgence : on s'arrête là, sans passer par les niveaux suivants.
"""

import unicodedata

from app.config.mots_cles_detresse import MOTS_CLES_DETRESSE

NUMEROS_URGENCE = {
    "numero_vert": "800 805 805",
    "samu": "1515",
    "sapeurs_pompiers": "18",
    "hopital": "Service de psychiatrie de l'Hôpital de Fann, Dakar",
}

REPONSE_URGENCE = (
    "Ce que vous décrivez me préoccupe. Vous n'êtes pas seul(e), et de l'aide existe, "
    "tout de suite : le numéro vert 800 805 805, le SAMU au 1515, ou le service de "
    "psychiatrie de l'Hôpital de Fann à Dakar. Un professionnel peut vous écouter "
    "maintenant. Sen Suivi ne remplace pas un professionnel de santé."
)


def _normaliser(texte: str) -> str:
    """Minuscules, sans accents : pour comparer sans dépendre de la saisie exacte."""
    sans_accents = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii')
    return sans_accents.lower()


def detecter_detresse(message: str) -> bool:
    """True si le message contient un signal de détresse (mots-clés niveau 0)."""
    normalise = _normaliser(message)
    return any(_normaliser(mot_cle) in normalise for mot_cle in MOTS_CLES_DETRESSE)
