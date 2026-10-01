"""Synthèse vocale : Titou peut répondre à voix haute.

On ne synthétise QUE des réponses déjà validées par les garde-fous (Django le
garantit avec un jeton signé par réponse). Le fournisseur est lu dans le .env
(API compatible OpenAI /audio/speech) ; s'il n'y en a pas, ou s'il échoue,
l'interface lit la réponse avec la voix française du navigateur. Le vocal est
un confort, jamais un point de panne : la réponse texte reste toujours affichée.
"""

import logging
import os

import httpx

journal = logging.getLogger(__name__)


class SyntheseIndisponible(Exception):
    pass


def reglages() -> dict:
    return {
        'url': (os.environ.get('SYNTHESE_URL_BASE') or '').rstrip('/'),
        'cle': os.environ.get('SYNTHESE_CLE_API', ''),
        'modele': os.environ.get('SYNTHESE_MODELE', ''),
        # Voix féminine francophone, si le fournisseur en propose une
        'voix': os.environ.get('SYNTHESE_VOIX', ''),
        'delai': float(os.environ.get('SYNTHESE_DELAI_SECONDES', '15')),
    }


def synthese_disponible() -> bool:
    r = reglages()
    return bool(r['url'] and r['cle'] and r['modele'])


def synthetiser(texte: str) -> bytes:
    """Audio MP3 du texte, ou SyntheseIndisponible."""
    r = reglages()
    if not synthese_disponible():
        raise SyntheseIndisponible('synthèse vocale non configurée')
    corps = {'model': r['modele'], 'input': texte, 'response_format': 'mp3'}
    if r['voix']:
        corps['voice'] = r['voix']
    try:
        reponse = httpx.post(
            f"{r['url']}/audio/speech", headers={'Authorization': f"Bearer {r['cle']}"}, json=corps, timeout=r['delai']
        )
        reponse.raise_for_status()
    except httpx.HTTPError as erreur:
        journal.warning('Synthèse vocale indisponible : %s', type(erreur).__name__)
        raise SyntheseIndisponible(type(erreur).__name__) from erreur
    if not reponse.content:
        raise SyntheseIndisponible('audio vide')
    return reponse.content
