"""Indexation des ressources publiées dans le RAG du microservice IA."""

import logging

import httpx
from django.conf import settings

from .models import Ressource, StatutRessource

journal = logging.getLogger(__name__)


def reindexer_rag() -> int:
    """Envoie toutes les ressources publiées au microservice IA ; renvoie le nombre indexé.

    Lève httpx.HTTPError si le microservice ne répond pas."""
    ressources = list(
        # Jamais un brouillon ni une proposition en attente : Titou ne cite que le publié
        Ressource.objects.filter(statut=StatutRessource.PUBLIEE).values('id', 'titre', 'contenu', 'thematique')
    )
    reponse = httpx.post(
        f'{settings.AI_SERVICE_URL}/reindexer', json=ressources, headers=settings.AI_SERVICE_ENTETES, timeout=120
    )
    reponse.raise_for_status()
    return reponse.json().get('ressources_indexees', 0)


def reindexer_sans_erreur() -> None:
    """Variante best-effort, pour un fil d'arrière-plan : une panne est seulement journalisée."""
    try:
        reindexer_rag()
    except httpx.HTTPError as erreur:
        journal.warning('Réindexation RAG impossible : %s', type(erreur).__name__)
