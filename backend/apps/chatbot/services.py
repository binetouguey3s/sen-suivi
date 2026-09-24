"""Appel au microservice IA : ce module ne calcule
rien lui-même, il transmet le message et renvoie la réponse déjà construite
par ai-service (règle validée ou ressource trouvée par le RAG)."""

import httpx
from django.conf import settings


class MicroserviceIAIndisponible(Exception):
    pass


def traiter_message(message: str) -> dict:
    try:
        reponse = httpx.post(
            f'{settings.AI_SERVICE_URL}/message', json={'message': message}, timeout=10
        )
        reponse.raise_for_status()
        return reponse.json()
    except httpx.HTTPError as erreur:
        raise MicroserviceIAIndisponible(str(erreur)) from erreur
