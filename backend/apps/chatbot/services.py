"""Appel au microservice IA : ce module ne calcule
rien lui-même, il transmet le message et renvoie la réponse déjà construite
par ai-service (règle validée ou ressource trouvée par le RAG)."""

import httpx
from django.conf import settings


class MicroserviceIAIndisponible(Exception):
    pass


class AudioRefuse(Exception):
    """Audio trop long, trop lourd ou dans un format non accepté."""


def transcrire(audio: bytes) -> dict:
    """Texte de l'enregistrement (en mémoire, jamais sur le disque)."""
    try:
        reponse = httpx.post(
            f'{settings.AI_SERVICE_URL}/transcrire',
            content=audio,
            headers={'Content-Type': 'application/octet-stream'},
            timeout=settings.AI_SERVICE_DELAI_SECONDES,
        )
    except httpx.HTTPError as erreur:
        raise MicroserviceIAIndisponible(type(erreur).__name__) from erreur
    if reponse.status_code in (413, 422):
        raise AudioRefuse(reponse.json().get('detail', 'Enregistrement refusé.'))
    if reponse.status_code != 200:
        raise MicroserviceIAIndisponible(str(reponse.status_code))
    return reponse.json()


def synthetiser(texte: str) -> bytes | None:
    """Audio d'une réponse déjà validée, ou None : l'interface lira alors le texte
    avec la voix du navigateur. Jamais d'erreur bloquante."""
    try:
        reponse = httpx.post(f'{settings.AI_SERVICE_URL}/reponse-vocale', json={'texte': texte}, timeout=20)
        return reponse.content if reponse.status_code == 200 else None
    except httpx.HTTPError:
        return None


def traiter_message(
    message: str, historique: list[dict] | None = None, profil: list[str] | None = None, suggestion_possible: bool = False
) -> dict:
    """`profil` : mots-clés du profil de tendance, seulement si l'utilisateur y a consenti.
    `suggestion_possible` : compte utilisateur connecté, à qui Django affichera
    le professionnel suggéré par l'algorithme d'orientation sous la réponse."""
    try:
        reponse = httpx.post(
            f'{settings.AI_SERVICE_URL}/message',
            json={
                'message': message,
                'historique': historique or [],
                'profil_tendance': profil or [],
                'suggestion_possible': suggestion_possible,
            },
            # Plus long que le budget de la cascade de modèles côté IA (LLM_DELAI_TOTAL_SECONDES)
            timeout=settings.AI_SERVICE_DELAI_SECONDES,
        )
        reponse.raise_for_status()
        return reponse.json()
    except httpx.HTTPError as erreur:
        raise MicroserviceIAIndisponible(str(erreur)) from erreur
