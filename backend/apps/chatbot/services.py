"""Appel au microservice IA : ce module ne calcule
rien lui-même, il transmet le message et renvoie la réponse déjà construite
par ai-service (règle validée ou ressource trouvée par le RAG)."""

import httpx
from django.conf import settings


class MicroserviceIAIndisponible(Exception):
    pass


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
