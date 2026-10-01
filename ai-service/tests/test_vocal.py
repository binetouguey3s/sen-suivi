"""Volet vocal : transcription et synthèse, sans aucun appel réel au fournisseur."""

import builtins
import tempfile

import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as main
import app.synthese_vocale as synthese
import app.transcription as transcription

client = TestClient(main.app)

WEBM = b'\x1a\x45\xdf\xa3' + b'\x00' * 2048


@pytest.fixture(autouse=True)
def fournisseur_factice(monkeypatch):
    monkeypatch.setenv('TRANSCRIPTION_URL_BASE', 'https://voix.test/v1')
    monkeypatch.setenv('TRANSCRIPTION_CLE_API', 'cle-de-test')
    monkeypatch.setenv('TRANSCRIPTION_MODELE', 'modele-de-transcription')
    monkeypatch.setenv('VOCAL_DUREE_MAX_SECONDES', '60')
    monkeypatch.setenv('VOCAL_TAILLE_MAX_MO', '10')
    for variable in ('SYNTHESE_URL_BASE', 'SYNTHESE_CLE_API', 'SYNTHESE_MODELE'):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(transcription.httpx, 'post', lambda *a, **k: pytest.fail('fournisseur appelé sans doublure'))


def transcription_qui_repond(monkeypatch, texte, duree=4.0):
    recu = {}

    def faux_post(url, headers, files, data, timeout):
        recu.update(files=files, data=data)
        return httpx.Response(200, json={'text': texte, 'duration': duree}, request=httpx.Request('POST', url))

    monkeypatch.setattr(transcription.httpx, 'post', faux_post)
    return recu


def envoyer(octets):
    return client.post('/transcrire', content=octets, headers={'Content-Type': 'audio/webm'})


def test_la_voix_est_transcrite_en_francais(monkeypatch):
    recu = transcription_qui_repond(monkeypatch, ' Bonjour, je suis fatiguée. ')

    corps = envoyer(WEBM).json()

    assert (corps['transcription'], corps['comprise']) == ('Bonjour, je suis fatiguée.', True)
    assert recu['data']['language'] == 'fr'
    assert recu['data']['model'] == 'modele-de-transcription'


# Test 5
def test_un_audio_trop_lourd_est_refuse_proprement(monkeypatch):
    monkeypatch.setenv('VOCAL_TAILLE_MAX_MO', '0.001')
    reponse = envoyer(WEBM)
    assert reponse.status_code == 413
    assert 'Mo' in reponse.json()['detail']


def test_un_audio_trop_long_est_refuse_proprement(monkeypatch):
    transcription_qui_repond(monkeypatch, 'Un très long message', duree=95)
    reponse = envoyer(WEBM)
    assert reponse.status_code == 422
    assert '60 secondes' in reponse.json()['detail']


@pytest.mark.parametrize('octets', [b'<html>pas du son</html>', b'%PDF-1.7 fichier', b''])
def test_un_format_non_accepte_est_refuse(octets):
    assert envoyer(octets).status_code == 422


@pytest.mark.parametrize(
    'entete', [b'OggS', b'RIFF\x00\x00\x00\x00WAVE', b'ID3', b'\x00\x00\x00\x18ftypM4A ']
)
def test_les_formats_courants_sont_reconnus(monkeypatch, entete):
    transcription_qui_repond(monkeypatch, 'Bonjour')
    assert envoyer(entete + b'\x00' * 64).status_code == 200


# Test 6
def test_une_transcription_de_detresse_declenche_le_niveau_0(monkeypatch):
    transcription_qui_repond(monkeypatch, 'Je veux mourir, je n’en peux plus.')
    monkeypatch.setattr(main, 'generer', lambda *a, **k: pytest.fail('modèle appelé sur une détresse'))
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: pytest.fail('modèle appelé sur une détresse'))

    texte = envoyer(WEBM).json()['transcription']
    # Le texte transcrit suit exactement le chemin d'un message tapé
    reponse = client.post('/message', json={'message': texte}).json()

    assert reponse['urgence'] is True
    assert '800 805 805' in reponse['reponse']


# Test 7
def test_l_audio_n_est_jamais_ecrit_sur_le_disque(monkeypatch):
    transcription_qui_repond(monkeypatch, 'Bonjour')

    def interdit(*args, **kwargs):
        raise AssertionError('écriture sur le disque interdite')

    ouvrir = builtins.open

    def ouvrir_en_lecture_seule(fichier, mode='r', *args, **kwargs):
        if any(m in mode for m in 'wax+'):
            raise AssertionError(f'écriture sur le disque interdite : {fichier}')
        return ouvrir(fichier, mode, *args, **kwargs)

    for nom in ('NamedTemporaryFile', 'TemporaryFile', 'SpooledTemporaryFile', 'mkstemp'):
        monkeypatch.setattr(tempfile, nom, interdit)
    monkeypatch.setattr(builtins, 'open', ouvrir_en_lecture_seule)

    assert envoyer(WEBM + b'\x00' * (3 * 1024 * 1024)).status_code == 200


def test_l_audio_n_apparait_jamais_dans_les_journaux(monkeypatch, caplog):
    def panne(*args, **kwargs):
        raise httpx.ConnectTimeout('délai dépassé')

    monkeypatch.setattr(transcription.httpx, 'post', panne)
    caplog.set_level('INFO')

    assert envoyer(WEBM).status_code == 503
    assert '\\x1a' not in caplog.text and 'voix.webm' not in caplog.text


@pytest.mark.parametrize('texte', ['', '...', ' ', '-', 'Sous-titrage Société Radio-Canada', "Merci d'avoir regardé !"])
def test_un_silence_n_est_jamais_devine(monkeypatch, texte):
    transcription_qui_repond(monkeypatch, texte)
    corps = envoyer(WEBM).json()
    assert corps['comprise'] is False
    assert 'réessayer' in corps['reponse_incomprise']


# Test 8
def test_un_echec_de_synthese_renvoie_503_et_jamais_une_erreur_bloquante():
    reponse = client.post('/reponse-vocale', json={'texte': 'Je vous écoute.'})
    assert reponse.status_code == 503


def test_la_synthese_renvoie_l_audio_de_la_reponse(monkeypatch):
    monkeypatch.setenv('SYNTHESE_URL_BASE', 'https://voix.test/v1')
    monkeypatch.setenv('SYNTHESE_CLE_API', 'cle')
    monkeypatch.setenv('SYNTHESE_MODELE', 'modele-voix')
    monkeypatch.setattr(
        synthese.httpx, 'post',
        lambda url, headers, json, timeout: httpx.Response(200, content=b'ID3audio', request=httpx.Request('POST', url)),
    )

    reponse = client.post('/reponse-vocale', json={'texte': 'Je vous écoute.'})

    assert (reponse.status_code, reponse.headers['content-type'], reponse.content) == (200, 'audio/mpeg', b'ID3audio')


def test_un_silence_detecte_par_le_modele_n_est_jamais_pris_pour_un_message(monkeypatch):
    def faux_post(url, headers, files, data, timeout):
        corps = {'text': 'Bonjour à tous', 'duration': 2, 'segments': [{'no_speech_prob': 0.93}]}
        return httpx.Response(200, json=corps, request=httpx.Request('POST', url))

    monkeypatch.setattr(transcription.httpx, 'post', faux_post)

    assert envoyer(WEBM).json()['comprise'] is False
