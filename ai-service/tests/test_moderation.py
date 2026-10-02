"""Modération du forum : on bloque l'AGRESSION, jamais la SOUFFRANCE.

Aucun appel réel au modèle : httpx.post est remplacé par monkeypatch.
"""

import json as json_module

import httpx
import pytest
from fastapi.testclient import TestClient

import app.main as main
import app.moderateur_forum as moderateur
from app.moderateur_forum import Decision, moderer, normaliser

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def modele_configure(monkeypatch):
    """Modèle factice configuré, cache vide ; aucun test n'atteint un vrai fournisseur."""
    monkeypatch.setenv('MODERATION_URL_BASE', 'https://moderation.test/v1')
    monkeypatch.setenv('MODERATION_CLE_API', 'cle-de-test')
    monkeypatch.setenv('MODERATION_MODELE', 'modele-de-moderation')
    monkeypatch.setenv('MODERATION_LONGUEUR_MIN', '20')
    moderateur._cache.clear()
    monkeypatch.setattr(moderateur.httpx, 'post', lambda *a, **k: pytest.fail('modèle appelé sans doublure'))


def modele_qui_repond(monkeypatch, categorie, gravite=1, extrait='', raison=''):
    appels = []

    def faux_post(url, headers, json, timeout):
        appels.append(json['messages'][-1]['content'])
        contenu = {'categorie': categorie, 'gravite': gravite, 'extrait_problematique': extrait, 'raison': raison}
        return httpx.Response(
            200, json={'choices': [{'message': {'content': json_module.dumps(contenu)}}]},
            request=httpx.Request('POST', url),
        )

    monkeypatch.setattr(moderateur.httpx, 'post', faux_post)
    return appels


# Test 9
@pytest.mark.parametrize('insulte', ['Espèce de connard', 'T es vraiment une s.a.l.o.p.e', 'c0nnaaard va', 'Yow danga dof'])
def test_une_insulte_evidente_est_bloquee_par_les_regles_sans_modele(insulte):
    resultat = moderer(insulte)

    assert (resultat.decision, resultat.categorie, resultat.niveau) == (Decision.BLOQUER, 'INSULTE', 'REGLES')
    assert 'reformuler' in resultat.message
    assert '«' not in resultat.message


def test_les_coordonnees_sont_citees_pour_savoir_quoi_retirer():
    assert '« 77 123 45 67 »' in moderer('Appelle-moi au 77 123 45 67').message


# Test 10
def test_un_temoignage_de_souffrance_est_publie(monkeypatch):
    modele_qui_repond(monkeypatch, 'DETRESSE', 3)

    resultat = moderer("Je me sens sale et nulle depuis des semaines, je ne sais plus quoi faire.")

    assert resultat.decision == Decision.PUBLIER_ACCOMPAGNER
    assert '800 805 805' in resultat.message


def test_les_mots_de_detresse_publient_et_accompagnent_sans_modele():
    resultat = moderer("je veux mourir, je n'en peux plus")
    assert (resultat.decision, resultat.categorie, resultat.niveau) == (Decision.PUBLIER_ACCOMPAGNER, 'DETRESSE', 'REGLES')


# Test 11
def test_un_recit_de_violence_subie_est_publie(monkeypatch):
    appels = modele_qui_repond(monkeypatch, 'CONFORME')

    resultat = moderer('Au lycée, ils me traitaient de salope tous les jours, j’en pleure encore.')

    # L'insulte rapportée ne bloque pas au niveau 0 : c'est le modèle qui tranche
    assert len(appels) == 1
    assert resultat.decision == Decision.PUBLIER


def test_se_decrire_durement_n_est_jamais_une_insulte(monkeypatch):
    modele_qui_repond(monkeypatch, 'CONFORME')
    assert moderer("Je me sens idiote et nulle de ne pas y arriver").decision == Decision.PUBLIER


# Test 12
def test_une_agression_dirigee_contre_un_membre_est_bloquee(monkeypatch):
    modele_qui_repond(monkeypatch, 'HARCELEMENT', 3, extrait='je vais venir te frapper')

    resultat = moderer("Toi qui défends ton oncle, je vais venir te frapper aussi.")

    assert resultat.decision == Decision.BLOQUER_PRIORITAIRE
    assert resultat.priorite == 2
    # L'admin voit l'extrait ; l'auteur, jamais ses propres mots blessants répétés
    assert resultat.extrait == 'je vais venir te frapper'
    assert 'frapper' not in resultat.message


# Test 13
@pytest.mark.parametrize(
    ('texte', 'extrait'),
    [
        ('Appelle-moi au 77 123 45 67 pour en parler', '77 123 45 67'),
        ('Écris-moi à fatou.diop@gmail.com', 'fatou.diop@gmail.com'),
        ('Mon insta c’est @fatou_d, ajoute-moi', '@fatou_d'),
    ],
)
def test_des_coordonnees_personnelles_sont_bloquees(texte, extrait):
    resultat = moderer(texte)
    assert (resultat.decision, resultat.categorie, resultat.extrait) == (Decision.BLOQUER, 'DONNEES_PERSONNELLES', extrait)


def test_les_numeros_d_ecoute_peuvent_etre_partages(monkeypatch):
    modele_qui_repond(monkeypatch, 'CONFORME')
    assert moderer('Le 800 805 805 m’a beaucoup aidée, appelez-les.').decision == Decision.PUBLIER


def test_le_spam_est_bloque_silencieusement():
    resultat = moderer('Code promo SENSUIVI sur www.boutique.sn/promo')
    assert (resultat.decision, resultat.message) == (Decision.BLOQUER_SILENCIEUX, '')


# Test 14
@pytest.mark.parametrize('panne', ['http', 'json', 'categorie'])
def test_le_modele_indisponible_envoie_en_file_humaine(monkeypatch, panne):
    def faux_post(url, headers, json, timeout):
        requete = httpx.Request('POST', url)
        if panne == 'http':
            raise httpx.ConnectTimeout('délai dépassé')
        contenu = 'pas du json' if panne == 'json' else '{"categorie": "INCONNUE", "gravite": 1}'
        return httpx.Response(200, json={'choices': [{'message': {'content': contenu}}]}, request=requete)

    monkeypatch.setattr(moderateur.httpx, 'post', faux_post)

    resultat = moderer('Un message assez long pour être envoyé au modèle de modération.')

    assert resultat.decision == Decision.ATTENTE_HUMAINE
    assert resultat.decision != Decision.PUBLIER


def test_sans_modele_configure_rien_n_est_publie_sans_controle(monkeypatch):
    monkeypatch.setenv('MODERATION_MODELE', '')
    assert moderer('Un message assez long pour être envoyé au modèle de modération.').decision == Decision.ATTENTE_HUMAINE


def test_souffrance_et_insulte_melees_partent_chez_un_humain_avec_accompagnement():
    resultat = moderer('Je veux mourir, vous êtes tous des connards')
    assert resultat.decision == Decision.ATTENTE_HUMAINE
    assert resultat.priorite == 2
    assert '800 805 805' in resultat.message


# --- Performance et coût --------------------------------------------------------

def test_un_message_court_sans_probleme_n_appelle_pas_le_modele():
    assert moderer('Merci beaucoup !').decision == Decision.PUBLIER


def test_un_message_identique_n_est_analyse_qu_une_fois(monkeypatch):
    appels = modele_qui_repond(monkeypatch, 'CONFORME')
    texte = 'Merci pour vos messages, ça fait du bien de lire que je ne suis pas seule.'

    moderer(texte)
    moderer(texte.upper())

    assert len(appels) == 1


def test_un_extrait_invente_par_le_modele_n_est_jamais_cite(monkeypatch):
    modele_qui_repond(monkeypatch, 'INSULTE', 2, extrait='phrase qui n’existe pas')
    assert moderer('Franchement ce que tu écris est ridicule et sans intérêt.').extrait == ''


def test_le_journal_ne_contient_jamais_le_texte(monkeypatch, caplog):
    modele_qui_repond(monkeypatch, 'CONFORME')
    caplog.set_level('INFO')

    moderer('Mon secret : je traverse une période très difficile en ce moment.')

    assert 'secret' not in caplog.text


def test_la_normalisation_dejoue_les_contournements():
    assert normaliser('C0NNAAARD') == ' conard '
    assert normaliser('s.a.l.o.p.e') == ' salope '
    assert normaliser('77 123 45 67') == ' 77 123 45 67 '


def test_la_route_de_moderation_renvoie_la_decision():
    corps = client.post('/moderer', json={'texte': 'Espèce de connard'}).json()
    assert (corps['decision'], corps['categorie']) == ('BLOQUER', 'INSULTE')
