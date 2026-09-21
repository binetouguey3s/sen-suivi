"""Le niveau 0 doit toujours primer, même sur un message qui contiendrait
aussi des mots-clés de stress ou de fatigue (aucun appel au RAG dans ce cas :
le test n'a donc pas besoin d'une base ChromaDB indexée)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_urgence_prime_sur_la_classification_d_intention():
    reponse = client.post(
        '/message',
        json={'message': "Je suis tellement stressé et fatigué que je veux en finir."},
    )
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps['urgence'] is True
    assert corps['source_reponse'] == 'REGLE'
    assert '800 805 805' in corps['reponse']
    assert '1515' in corps['reponse']


def test_endpoint_sante():
    assert client.get('/health').json() == {'statut': 'ok'}
