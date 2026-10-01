"""Outils du chatbot vocal : audio gardé en mémoire, jeton de lecture à voix haute.

CONFIDENTIALITÉ : l'audio n'est jamais écrit sur le disque. Par défaut, Django
place sur le disque tout fichier envoyé de plus de 2,5 Mo ; ce gestionnaire le
garde en mémoire quelle que soit sa taille (plafonnée par VOCAL_TAILLE_MAX_MO),
et il disparaît avec la requête.
"""

import hashlib

from django.conf import settings
from django.core import signing
from django.core.files.uploadhandler import MemoryFileUploadHandler, StopUpload

_SEL = 'sen-suivi.reponse-vocale'
JETON_VOCAL_DUREE_SECONDES = 3600


class AudioEnMemoireUploadHandler(MemoryFileUploadHandler):
    """Garde l'enregistrement en mémoire, jamais dans un fichier temporaire."""

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        # Toujours actif, même au-delà du seuil habituel de Django
        self.activated = True

    def receive_data_chunk(self, raw_data, start):
        if start + len(raw_data) > settings.VOCAL_TAILLE_MAX_MO * 1024 * 1024:
            raise StopUpload(connection_reset=True)
        return super().receive_data_chunk(raw_data, start)


def _empreinte(texte: str) -> str:
    return hashlib.sha256(texte.encode()).hexdigest()


def jeton_vocal(reponse: str) -> str:
    """Remis avec chaque réponse de Titou : seule une réponse passée par les
    garde-fous peut ensuite être lue à voix haute."""
    return signing.TimestampSigner(salt=_SEL).sign(_empreinte(reponse))


def jeton_vocal_valide(texte: str, jeton: str) -> bool:
    try:
        empreinte = signing.TimestampSigner(salt=_SEL).unsign(jeton or '', max_age=JETON_VOCAL_DUREE_SECONDES)
    except signing.BadSignature:
        return False
    return empreinte == _empreinte(texte)
