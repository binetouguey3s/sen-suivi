"""Vecteurs du RAG par l'API Mistral (hébergement gratuit, sans PyTorch)."""

import app.moteur_rag as rag


class FausseReponse:
    def raise_for_status(self):
        pass

    def json(self):
        # L'API peut renvoyer les vecteurs dans le désordre : l'index fait foi
        return {'data': [{'index': 1, 'embedding': [0.0, 1.0]}, {'index': 0, 'embedding': [1.0, 0.0]}]}


def test_les_vecteurs_sont_demandes_a_mistral_dans_l_ordre(monkeypatch):
    appels = {}

    def faux_post(url, headers, json, timeout):
        appels.update(url=url, headers=headers, json=json)
        return FausseReponse()

    monkeypatch.setenv('MISTRAL_CLE_API', 'cle-test')
    monkeypatch.setenv('MISTRAL_URL_BASE', 'https://api.mistral.ai/v1/')
    monkeypatch.setattr(rag.httpx, 'post', faux_post)

    vecteurs = rag.EmbeddingsMistral('mistral-embed')(['premier', 'second'])

    assert [list(v) for v in vecteurs] == [[1.0, 0.0], [0.0, 1.0]]
    assert appels['url'] == 'https://api.mistral.ai/v1/embeddings'
    assert appels['headers'] == {'Authorization': 'Bearer cle-test'}
    assert appels['json'] == {'model': 'mistral-embed', 'input': ['premier', 'second']}


def test_le_fournisseur_mistral_n_a_pas_besoin_de_pytorch(monkeypatch):
    monkeypatch.setattr(rag, 'EMBEDDING_FOURNISSEUR', 'mistral')
    assert isinstance(rag._fonction_embeddings(), rag.EmbeddingsMistral)
