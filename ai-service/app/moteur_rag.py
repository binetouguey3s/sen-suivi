"""Niveau 2 du chatbot : RAG (docs/CONTEXTE.md section 2 et section 2 du stack : ChromaDB).

Recherche par similarité dans les ressources validées de la plateforme.
Le chatbot ne construit jamais de texte libre à ce niveau : il renvoie la
ressource la plus proche, telle qu'elle existe dans la bibliothèque.
"""

import os

import chromadb

CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', '/data/chroma')
SEUIL_SIMILARITE_RAG = float(os.environ.get('SEUIL_SIMILARITE_RAG', '0.40'))
NOMBRE_MAX_RESULTATS = 3

_client = None
_collection = None


def _obtenir_collection():
    """Connexion paresseuse : évite d'ouvrir la base au chargement du module
    (utile pour les tests, qui n'ont pas toujours besoin du RAG)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        # Espace cosinus : la distance renvoyée par Chroma devient directement
        # comparable au seuil de similarité (similarite = 1 - distance).
        _collection = _client.get_or_create_collection(
            name='ressources', metadata={'hnsw:space': 'cosine'}
        )
    return _collection


def indexer_ressources(ressources: list[dict]) -> int:
    """Synchronise l'index avec la liste fournie (id, titre, contenu, thematique).

    Les ressources supprimées côté Django disparaissent aussi de l'index :
    appelée par POST /reindexer (workflow n8n « indexation RAG » ou commande
    manuelle) avec la liste complète des ressources.
    """
    collection = _obtenir_collection()
    ids = [str(r['id']) for r in ressources]
    obsoletes = [i for i in collection.get()['ids'] if i not in ids]
    if obsoletes:
        collection.delete(ids=obsoletes)
    if not ressources:
        return 0
    collection.upsert(
        ids=ids,
        documents=[f"{r['titre']}\n{r['contenu']}" for r in ressources],
        metadatas=[
            {'titre': r['titre'], 'thematique': r['thematique'], 'ressource_id': r['id']}
            for r in ressources
        ],
    )
    return len(ressources)


def rechercher(message: str) -> dict | None:
    """La ressource la plus proche du message, si elle dépasse le seuil de similarité."""
    collection = _obtenir_collection()
    if collection.count() == 0:
        return None

    resultats = collection.query(
        query_texts=[message],
        n_results=min(NOMBRE_MAX_RESULTATS, collection.count()),
        include=['metadatas', 'distances'],
    )
    if not resultats['ids'][0]:
        return None

    meilleure_distance = resultats['distances'][0][0]
    similarite = 1 - meilleure_distance
    if similarite < SEUIL_SIMILARITE_RAG:
        return None

    metadonnees = resultats['metadatas'][0][0]
    return {
        'ressource_id': metadonnees['ressource_id'],
        'titre': metadonnees['titre'],
        'thematique': metadonnees['thematique'],
        'similarite': round(similarite, 2),
    }
