"""Transcription de la voix (volet vocal).

L'audio n'est JAMAIS écrit sur le disque ni journalisé : il arrive en mémoire
(corps brut de la requête), part en mémoire vers le modèle de transcription
(TRANSCRIPTION_MODELE du .env), puis n'est plus référencé nulle part.

Le texte obtenu suit ensuite exactement le même chemin qu'un message tapé :
détection de détresse d'abord, puis intention, ressources, génération,
validation et repli. Aucun raccourci.
"""

import logging
import os
from dataclasses import dataclass

import httpx

journal = logging.getLogger(__name__)

# Formats acceptés : signature des premiers octets, pour ne jamais se fier au seul type annoncé
FORMATS = {
    'webm': ('audio/webm', lambda o: o[:4] == b'\x1a\x45\xdf\xa3'),
    'ogg': ('audio/ogg', lambda o: o[:4] == b'OggS'),
    'wav': ('audio/wav', lambda o: o[:4] == b'RIFF' and o[8:12] == b'WAVE'),
    'mp3': ('audio/mpeg', lambda o: o[:3] == b'ID3' or (len(o) > 1 and o[0] == 0xFF and o[1] & 0xE0 == 0xE0)),
    'm4a': ('audio/mp4', lambda o: o[4:8] == b'ftyp'),
}


# Phrases que les modèles de transcription « entendent » dans un silence ou un
# bruit, héritées des sous-titres de leur entraînement : jamais prises pour un message
HALLUCINATIONS = [
    'sous-titrage', 'sous-titres', 'radio-canada', 'amara.org', "merci d'avoir regardé",
    'abonnez-vous', 'st 501', 'sous titrage',
]
# Au-delà, Whisper estime qu'aucun segment ne contient de parole
PROBABILITE_SILENCE_MAX = 0.6


class AudioRefuse(Exception):
    """Audio trop long, trop lourd ou dans un format non accepté."""


class TranscriptionIndisponible(Exception):
    pass


@dataclass
class Transcription:
    texte: str
    duree: float | None


def reglages() -> dict:
    return {
        'url': (os.environ.get('TRANSCRIPTION_URL_BASE') or os.environ.get('LLM_URL_BASE', '')).rstrip('/'),
        'cle': os.environ.get('TRANSCRIPTION_CLE_API') or os.environ.get('LLM_CLE_API', ''),
        'modele': os.environ.get('TRANSCRIPTION_MODELE', ''),
        'duree_max': float(os.environ.get('VOCAL_DUREE_MAX_SECONDES', '60')),
        'taille_max': int(float(os.environ.get('VOCAL_TAILLE_MAX_MO', '10')) * 1024 * 1024),
        'delai': float(os.environ.get('TRANSCRIPTION_DELAI_SECONDES', '20')),
    }


def format_audio(octets: bytes) -> str:
    """Extension du format reconnu, ou AudioRefuse."""
    for extension, (_, reconnait) in FORMATS.items():
        if reconnait(octets):
            return extension
    raise AudioRefuse('Format audio non accepté (webm, ogg, mp3, wav ou m4a).')


def verifier(octets: bytes) -> str:
    r = reglages()
    if not octets:
        raise AudioRefuse('Aucun son reçu.')
    if len(octets) > r['taille_max']:
        raise AudioRefuse(f"L'enregistrement dépasse {r['taille_max'] // (1024 * 1024)} Mo.")
    return format_audio(octets)


def transcrire(octets: bytes) -> Transcription:
    """Texte de l'enregistrement, en français. Lève AudioRefuse ou TranscriptionIndisponible."""
    extension = verifier(octets)
    r = reglages()
    if not (r['url'] and r['cle'] and r['modele']):
        raise TranscriptionIndisponible('modèle de transcription non configuré')
    try:
        reponse = httpx.post(
            f"{r['url']}/audio/transcriptions",
            headers={'Authorization': f"Bearer {r['cle']}"},
            # Tout reste en mémoire : l'audio est passé comme octets, jamais comme fichier
            files={'file': (f'voix.{extension}', octets, FORMATS[extension][0])},
            data={'model': r['modele'], 'language': 'fr', 'response_format': 'verbose_json', 'temperature': '0'},
            timeout=r['delai'],
        )
        reponse.raise_for_status()
        corps = reponse.json()
    except (httpx.HTTPError, ValueError) as erreur:
        # Jamais l'audio ni le texte dans les journaux : seulement le type d'erreur
        journal.warning('Transcription indisponible : %s', type(erreur).__name__)
        raise TranscriptionIndisponible(type(erreur).__name__) from erreur
    duree = corps.get('duration')
    if duree is not None and float(duree) > r['duree_max'] + 2:
        raise AudioRefuse(f"L'enregistrement dépasse {int(r['duree_max'])} secondes.")
    segments = corps.get('segments') or []
    if segments and all(float(seg.get('no_speech_prob', 0)) > PROBABILITE_SILENCE_MAX for seg in segments):
        return Transcription(texte='', duree=duree)
    return Transcription(texte=(corps.get('text') or '').strip(), duree=duree)


def comprehensible(texte: str) -> bool:
    """Au moins un vrai mot : un silence ou un bruit ne doit jamais être deviné."""
    lettres = sum(c.isalpha() for c in texte)
    if lettres < 2 or texte.strip(' .…!?-') == '':
        return False
    minuscules = texte.lower().replace('’', "'")
    return not any(phrase in minuscules for phrase in HALLUCINATIONS)
