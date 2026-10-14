"""Audio des podcasts : texte à lire et synthèse par le microservice IA.

Le texte d'une ressource suit le format de la bibliothèque : « ## » pour un
intertitre (lu comme une pause), « > » pour une citation (lue normalement).
La synthèse passe par l'endpoint /reponse-vocale d'ai-service, qui accepte
3 000 caractères au plus : le texte est donc découpé en morceaux, et les MP3
obtenus sont mis bout à bout.
"""

import re

import httpx
from django.conf import settings

# Sous la limite d'ai-service (TexteASynthetiser : 3 000 caractères)
TAILLE_MORCEAU = 2800
DELAI_SYNTHESE_SECONDES = 60


class SyntheseIndisponible(Exception):
    """Synthèse vocale non configurée ou en échec : rien n'est écrit."""


def texte_a_lire(titre: str, contenu: str) -> str:
    """Le titre, puis le contenu, prêts à être lus à voix haute.

    Un intertitre devient une phrase isolée, suivie d'une pause (un paragraphe
    à lui seul, terminé par un point) ; le chevron des citations disparaît.
    """
    paragraphes = [titre.rstrip('.') + '.']
    for bloc in re.split(r'\n\s*\n', contenu.strip()):
        bloc = bloc.strip()
        if not bloc:
            continue
        if bloc.startswith('##'):
            bloc = bloc.lstrip('#').strip().rstrip('.:') + '.'
        else:
            bloc = re.sub(r'^>\s?', '', bloc, flags=re.MULTILINE)
        paragraphes.append(' '.join(bloc.split()))
    return '\n\n'.join(paragraphes)


def morceaux(texte: str, taille: int = TAILLE_MORCEAU) -> list[str]:
    """Découpe aux paragraphes, puis aux phrases si un paragraphe est trop long."""
    resultat: list[str] = []
    courant = ''
    for paragraphe in texte.split('\n\n'):
        phrases = re.split(r'(?<=[.!?…])\s+', paragraphe) if len(paragraphe) > taille else [paragraphe]
        for phrase in phrases:
            for debut in range(0, len(phrase), taille):  # phrase démesurée : coupée en dernier recours
                partie = phrase[debut:debut + taille]
                if courant and len(courant) + 2 + len(partie) > taille:
                    resultat.append(courant)
                    courant = partie
                else:
                    courant = f'{courant}\n\n{partie}' if courant else partie
    if courant:
        resultat.append(courant)
    return resultat


def synthetiser(texte: str) -> bytes:
    """MP3 de tout le texte, morceau par morceau, ou SyntheseIndisponible."""
    audio = b''
    for morceau in morceaux(texte):
        try:
            reponse = httpx.post(
                f'{settings.AI_SERVICE_URL}/reponse-vocale', json={'texte': morceau}, timeout=DELAI_SYNTHESE_SECONDES
            )
        except httpx.HTTPError as erreur:
            raise SyntheseIndisponible(f'microservice IA injoignable ({type(erreur).__name__})') from erreur
        if reponse.status_code != 200 or not reponse.content:
            raise SyntheseIndisponible('synthèse vocale non configurée ou en échec (SYNTHESE_* dans le .env)')
        audio += reponse.content
    return audio
