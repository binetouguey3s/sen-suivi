"""Pipeline complet avec le niveau 2b : aucun appel réel au fournisseur,
le modèle et le RAG sont remplacés par monkeypatch."""

import httpx
import pytest
from fastapi.testclient import TestClient

import app.generateur_reponse as generateur
import app.main as main

client = TestClient(main.app)

RESSOURCE = {
    'ressource_id': 7,
    'titre': 'Respirer avant un examen',
    'thematique': 'Respiration',
    'contenu': 'Inspirez sur quatre temps, expirez sur six.',
    'similarite': 0.8,
}

REPONSE_EMPATHIQUE = (
    "Vous avez l'impression que tout s'accélère à l'approche de l'épreuve. Beaucoup de "
    "personnes traversent cela. « Respirer avant un examen » propose d'inspirer sur quatre "
    "temps puis d'expirer sur six pour ralentir. Voulez-vous essayer maintenant ?"
)


def modele(texte):
    """Doublure du modèle : comme le vrai, sa réponse passe par le contrôle
    `accepter` (le validateur) avant d'être retenue."""

    def repondre(*args, **kwargs):
        accepter = kwargs.get('accepter')
        return texte if accepter is None or accepter(texte) else None

    return repondre


@pytest.fixture(autouse=True)
def isoler_des_fournisseurs(monkeypatch):
    """Le conteneur de test charge les vraies clés du .env : sans ces doublures,
    un test pourrait appeler réellement un fournisseur. Aucun test ne le fait."""
    monkeypatch.setattr(main, 'catalogue', lambda: [])
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: None)
    monkeypatch.setattr(main, 'generer', lambda *a, **k: None)


@pytest.fixture
def pipeline(monkeypatch):
    """RAG qui trouve une ressource, modèle disponible : on choisit ensuite sa réponse."""
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [RESSOURCE])
    monkeypatch.setattr(main, 'rechercher', lambda message: RESSOURCE)
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)

    def fixer_reponse(texte):
        monkeypatch.setattr(main, 'generer', modele(texte))

    return fixer_reponse


def envoyer(message):
    return client.post('/message', json={'message': message}).json()


def test_un_message_de_detresse_n_atteint_jamais_le_modele(pipeline, monkeypatch):
    def interdit(*args, **kwargs):
        raise AssertionError('Le modèle de langage a été appelé sur un message de détresse')

    monkeypatch.setattr(main, 'generer', interdit)
    monkeypatch.setattr(generateur.httpx, 'post', interdit)

    corps = envoyer("Je n'en peux plus, je veux en finir.")

    assert corps['urgence'] is True
    assert '800 805 805' in corps['reponse']


def test_une_reponse_generee_valide_est_renvoyee(pipeline):
    pipeline(REPONSE_EMPATHIQUE)

    corps = envoyer("J'ai l'impression que tout va trop vite avant l'épreuve de demain")

    assert corps['source_reponse'] == 'GENERATION'
    assert corps['reponse'] == REPONSE_EMPATHIQUE
    assert corps['ressource']['ressource_id'] == 7


def test_une_reponse_avec_formule_creuse_bascule_sur_le_repli(pipeline):
    pipeline('Je comprends, courage ! ' + REPONSE_EMPATHIQUE)

    corps = envoyer("J'ai l'impression que tout va trop vite avant l'épreuve de demain")

    assert corps['source_reponse'] == 'RAG'
    assert 'Respirer avant un examen' in corps['reponse']


def test_une_reponse_avec_terme_clinique_bascule_sur_le_repli(pipeline):
    pipeline("Cela ressemble à un trouble du sommeil. La ressource peut aider.")

    assert envoyer("Je me réveille plusieurs fois chaque nuit ces temps-ci")['source_reponse'] == 'RAG'


def test_sans_ressource_le_mode_ecoute_repond(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'generer', lambda *a: pytest.fail('mode ressources appelé sans ressource'))
    monkeypatch.setattr(
        main,
        'ecouter',
        modele("Bonjour, je suis Titou, l'assistant d'écoute de Sen Suivi. Comment vous sentez-vous aujourd'hui ?"),
    )

    corps = envoyer('bonjour')

    assert corps['source_reponse'] == 'GENERATION'
    assert corps['reponse'].startswith('Bonjour, je suis Titou')
    assert corps['ressource'] is None


def test_une_reponse_d_ecoute_qui_conseille_en_liste_est_rejetee(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    monkeypatch.setattr(main, 'ecouter', modele('Voici mes conseils :\n- dormir\n- respirer.'))

    assert envoyer('Je ne sais pas trop quoi dire')['reponse'] == main.REPONSE_REPLI


def test_sans_modele_ni_ressource_le_repli_relance_la_conversation(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)

    corps = envoyer('bonjour')

    assert corps['reponse'] == main.REPONSE_REPLI
    assert '?' in corps['reponse']


def test_l_historique_de_la_conversation_est_transmis(pipeline, monkeypatch):
    recu = {}

    def generer_espion(message, ressources, historique, *reste, **options):
        recu['historique'] = historique
        return REPONSE_EMPATHIQUE

    monkeypatch.setattr(main, 'generer', generer_espion)
    historique = [
        {'auteur': 'UTILISATEUR', 'contenu': "J'ai un examen demain"},
        {'auteur': 'BOT', 'contenu': 'Comment vous sentez-vous à son approche ?'},
    ]

    client.post('/message', json={'message': 'Tout va trop vite', 'historique': historique})

    assert recu['historique'] == historique


def test_l_historique_ne_retarde_jamais_une_reponse_d_urgence(pipeline, monkeypatch):
    monkeypatch.setattr(main, 'generer', lambda *a: pytest.fail('modèle appelé sur une détresse'))
    historique = [{'auteur': 'UTILISATEUR', 'contenu': 'Bonjour'}] * 5

    corps = client.post('/message', json={'message': 'Je veux en finir', 'historique': historique}).json()

    assert corps['urgence'] is True


def test_modele_indisponible_repli_sur_la_ressource(pipeline, monkeypatch):
    monkeypatch.setattr(main, 'generer', lambda *a, **k: None)

    corps = envoyer("J'ai l'impression que tout va trop vite avant l'épreuve de demain")

    assert corps['source_reponse'] == 'RAG'
    assert corps['ressource']['ressource_id'] == 7


def test_le_generateur_essaie_le_modele_de_secours(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', 'modele-principal')
    monkeypatch.setenv('LLM_MODELE_SECOURS', 'modele-secours')
    appels = []

    def faux_post(url, headers, json, timeout):
        appels.append(json['model'])
        requete = httpx.Request('POST', url)
        if json['model'] == 'modele-principal':
            return httpx.Response(503, request=requete)
        return httpx.Response(200, json={'choices': [{'message': {'content': ' Réponse. '}}]}, request=requete)

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)

    assert generateur.generer('Bonjour', [RESSOURCE]) == 'Réponse.'
    assert appels == ['modele-principal', 'modele-secours']


def test_le_generateur_ne_leve_jamais_d_exception(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', 'modele-principal')
    monkeypatch.delenv('LLM_MODELE_SECOURS', raising=False)

    def panne(*args, **kwargs):
        raise httpx.ConnectTimeout('délai dépassé')

    monkeypatch.setattr(generateur.httpx, 'post', panne)

    assert generateur.generer('Bonjour', [RESSOURCE]) is None


def test_le_modele_desactive_n_est_jamais_appele(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'false')
    monkeypatch.setattr(generateur.httpx, 'post', lambda *a, **k: pytest.fail('appel alors que LLM_ACTIVE=false'))

    assert generateur.generer('Bonjour', [RESSOURCE]) is None


def test_la_cascade_passe_au_fournisseur_suivant(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'GROQ,MISTRAL')
    for prefixe, modele in (('GROQ', 'modele-groq'), ('MISTRAL', 'modele-mistral')):
        monkeypatch.setenv(f'{prefixe}_URL_BASE', f'https://{prefixe.lower()}.test/v1')
        monkeypatch.setenv(f'{prefixe}_CLE_API', 'cle-de-test')
        monkeypatch.setenv(f'{prefixe}_MODELE', modele)
        monkeypatch.delenv(f'{prefixe}_MODELE_SECOURS', raising=False)
    appels = []

    def faux_post(url, headers, json, timeout):
        appels.append(url)
        requete = httpx.Request('POST', url)
        if 'groq' in url:
            return httpx.Response(429, request=requete)
        return httpx.Response(200, json={'choices': [{'message': {'content': 'Bonjour.'}}]}, request=requete)

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)

    assert generateur.ecouter('bonjour') == 'Bonjour.'
    assert appels == ['https://groq.test/v1/chat/completions', 'https://mistral.test/v1/chat/completions']


def test_la_reflexion_interne_du_modele_est_retiree(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', 'modele-qui-reflechit')
    monkeypatch.setenv('LLM_EFFORT_RAISONNEMENT', 'low')
    monkeypatch.delenv('LLM_MODELE_SECOURS', raising=False)
    envois = []

    def faux_post(url, headers, json, timeout):
        envois.append(json)
        contenu = '<think>La personne semble inquiète…</think>Bonjour, comment allez-vous ?'
        return httpx.Response(200, json={'choices': [{'message': {'content': contenu}}]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)

    assert generateur.ecouter('bonjour') == 'Bonjour, comment allez-vous ?'
    assert envois[0]['reasoning_effort'] == 'low'


def test_le_budget_de_temps_total_est_respecte(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', 'lent')
    monkeypatch.setenv('LLM_MODELE_SECOURS', 'jamais-essaye')
    monkeypatch.setenv('LLM_DELAI_TOTAL_SECONDES', '5')
    horloge = iter([0.0, 0.0, 4.5])  # le premier essai consomme 4,5 s sur 5
    monkeypatch.setattr(generateur.time, 'monotonic', lambda: next(horloge))
    essais = []

    def lent(url, headers, json, timeout):
        essais.append(json['model'])
        raise httpx.ReadTimeout('trop long')

    monkeypatch.setattr(generateur.httpx, 'post', lent)

    assert generateur.ecouter('bonjour') is None
    assert essais == ['lent']


def test_chaque_modele_recoit_son_propre_effort_de_raisonnement(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', 'principal')
    monkeypatch.setenv('LLM_EFFORT_RAISONNEMENT', 'none')
    monkeypatch.setenv('LLM_MODELE_SECOURS', 'secours')
    monkeypatch.setenv('LLM_EFFORT_RAISONNEMENT_SECOURS', 'low')
    efforts = {}

    def faux_post(url, headers, json, timeout):
        efforts[json['model']] = json.get('reasoning_effort')
        # Le principal répond vide : le secours doit être essayé avec son propre réglage
        contenu = '' if json['model'] == 'principal' else 'Bonjour.'
        return httpx.Response(200, json={'choices': [{'message': {'content': contenu}}]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)

    assert generateur.ecouter('bonjour') == 'Bonjour.'
    assert efforts == {'principal': 'none', 'secours': 'low'}


# --- Conversation : repli vers l'écoute, intentions, catalogue ------------------

def test_une_reponse_rejetee_en_mode_ressources_passe_au_mode_ecoute(pipeline, monkeypatch):
    pipeline('Bon courage ! ' + REPONSE_EMPATHIQUE)
    monkeypatch.setattr(main, 'ecouter', modele("Ce qui se passe avant l'épreuve semble vous peser."))

    corps = envoyer("J'ai l'impression que tout va trop vite avant l'épreuve de demain")

    assert corps['source_reponse'] == 'GENERATION'
    assert corps['reponse'] == "Ce qui se passe avant l'épreuve semble vous peser."


def test_une_intention_reconnue_avec_un_modele_donne_une_reponse_qui_suit_la_conversation(pipeline):
    pipeline(REPONSE_EMPATHIQUE)

    corps = envoyer('Je suis fatiguée')

    assert corps['source_reponse'] == 'GENERATION'
    assert corps['intention'] == 'FATIGUE'


def test_sans_reponse_du_modele_l_intention_retombe_sur_sa_reponse_predefinie(pipeline, monkeypatch):
    monkeypatch.setattr(main, 'generer', lambda *a, **k: None)

    corps = envoyer('Je suis fatiguée')

    assert corps['source_reponse'] == 'REGLE'
    assert corps['reponse'] == main.REPONSE_PAR_INTENTION['FATIGUE']


def test_sans_modele_l_intention_donne_sa_reponse_predefinie(monkeypatch):
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)
    monkeypatch.setattr(main, 'rechercher', lambda message: None)

    corps = envoyer('Je suis fatiguée')

    assert (corps['source_reponse'], corps['reponse']) == ('REGLE', main.REPONSE_PAR_INTENTION['FATIGUE'])


def test_le_catalogue_des_ressources_est_transmis_au_modele(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    catalogue = [{'ressource_id': 3, 'titre': 'Dormir mieux', 'thematique': 'Sommeil'}]
    monkeypatch.setattr(main, 'catalogue', lambda: catalogue)
    recu = {}

    def ecouter_espion(message, historique, liste, echeance, **options):
        recu['catalogue'] = liste
        return "Voici d'autres ressources : « Dormir mieux »."

    monkeypatch.setattr(main, 'ecouter', ecouter_espion)

    envoyer("Y a-t-il d'autres ressources ?")

    assert recu['catalogue'] == catalogue


def test_un_catalogue_indisponible_ne_bloque_pas_la_reponse(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)

    def panne():
        raise RuntimeError('ChromaDB indisponible')

    monkeypatch.setattr(main, 'catalogue', panne)
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: 'Bonjour, comment allez-vous ?')

    assert envoyer('bonjour')['reponse'] == 'Bonjour, comment allez-vous ?'


# --- Encart de ressource : seulement celle dont la réponse parle -----------------

AUTRE = {'ressource_id': 9, 'titre': 'Gérer la pression familiale sans culpabiliser', 'thematique': 'Famille',
         'contenu': 'Poser des limites avec bienveillance face aux attentes de la famille.', 'similarite': 0.5}


def test_l_encart_montre_la_ressource_dont_le_titre_est_cite():
    texte = "La bibliothèque propose « Gérer la pression familiale sans culpabiliser » pour en parler."
    assert main.ressource_evoquee(texte, [RESSOURCE, AUTRE])['ressource_id'] == 9


def test_aucun_encart_sans_titre_cite_meme_si_le_contenu_est_repris():
    texte = "Vous pourriez inspirer sur quatre temps puis expirer sur six pour ralentir."
    assert main.ressource_evoquee(texte, [AUTRE, RESSOURCE]) is None


def test_aucun_encart_si_la_reponse_ne_parle_d_aucune_ressource():
    texte = "Je n'ai pas de ressource qui corresponde vraiment à votre situation. Voulez-vous en parler ?"
    assert main.ressource_evoquee(texte, [RESSOURCE, AUTRE]) is None


def test_une_reponse_qui_se_repete_passe_au_mode_ecoute(pipeline, monkeypatch):
    pipeline(REPONSE_EMPATHIQUE)
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: 'Qu’est-ce qui pèse le plus aujourd’hui ?')
    historique = [{'auteur': 'UTILISATEUR', 'contenu': 'Je suis fatiguée'}, {'auteur': 'BOT', 'contenu': REPONSE_EMPATHIQUE}]

    corps = client.post('/message', json={'message': 'Je veux sortir de cette fatigue', 'historique': historique}).json()

    assert corps['reponse'] == 'Qu’est-ce qui pèse le plus aujourd’hui ?'


def test_une_reponse_tronquee_n_est_jamais_affichee(monkeypatch):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', 'coupe')
    monkeypatch.setenv('LLM_MODELE_SECOURS', 'complet')
    monkeypatch.delenv('LLM_EFFORT_RAISONNEMENT', raising=False)

    def faux_post(url, headers, json, timeout):
        coupe = json['model'] == 'coupe'
        choix = {'message': {'content': 'Voici « Parler de ce qu’on' if coupe else 'Réponse complète.'},
                 'finish_reason': 'length' if coupe else 'stop'}
        return httpx.Response(200, json={'choices': [choix]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)

    assert generateur.ecouter('Y a-t-il d’autres ressources ?') == 'Réponse complète.'


# --- Réponses coupées et repli -------------------------------------------------

def _un_fournisseur(monkeypatch, principal, secours):
    monkeypatch.setenv('LLM_ACTIVE', 'true')
    monkeypatch.setenv('LLM_FOURNISSEURS', 'LLM')
    monkeypatch.setenv('LLM_URL_BASE', 'https://fournisseur.test/v1')
    monkeypatch.setenv('LLM_CLE_API', 'cle-de-test')
    monkeypatch.setenv('LLM_MODELE', principal)
    monkeypatch.setenv('LLM_MODELE_SECOURS', secours)
    monkeypatch.delenv('LLM_EFFORT_RAISONNEMENT', raising=False)
    monkeypatch.delenv('LLM_EFFORT_RAISONNEMENT_SECOURS', raising=False)


def test_une_phrase_coupee_malgre_une_fin_normale_passe_au_modele_suivant(monkeypatch):
    _un_fournisseur(monkeypatch, 'coupe', 'complet')

    def faux_post(url, headers, json, timeout):
        texte = 'Vous pouvez demander une' if json['model'] == 'coupe' else 'Vous pouvez demander une mise en relation.'
        choix = {'message': {'content': texte}, 'finish_reason': 'stop'}
        return httpx.Response(200, json={'choices': [choix]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)

    assert generateur.ecouter('une quoi ?') == 'Vous pouvez demander une mise en relation.'


def test_une_reponse_refusee_par_le_validateur_passe_au_modele_suivant(monkeypatch):
    _un_fournisseur(monkeypatch, 'creux', 'juste')

    def faux_post(url, headers, json, timeout):
        texte = 'Je comprends, bon courage.' if json['model'] == 'creux' else 'Cette fatigue semble peser sur vos journées.'
        return httpx.Response(200, json={'choices': [{'message': {'content': texte}}]}, request=httpx.Request('POST', url))

    monkeypatch.setattr(generateur.httpx, 'post', faux_post)
    accepter = lambda texte: main.valider(texte, [], 'ecoute').valide  # noqa: E731

    assert generateur.ecouter('je suis épuisée', accepter=accepter) == 'Cette fatigue semble peser sur vos journées.'


def test_une_reponse_coupee_de_l_historique_n_est_pas_transmise_au_modele():
    historique = [
        {'auteur': 'UTILISATEUR', 'contenu': 'oui je veux une mise en relation'},
        {'auteur': 'BOT', 'contenu': "Vous pouvez consulter l'annuaire pour demander une"},
        {'auteur': 'UTILISATEUR', 'contenu': 'une quoi ?'},
    ]

    messages = generateur._messages_historique(historique)

    assert [m['role'] for m in messages] == ['user', 'user']


def test_le_repli_n_est_jamais_envoye_deux_fois_de_suite(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: False)
    historique = [{'auteur': 'UTILISATEUR', 'contenu': 'bof'}, {'auteur': 'BOT', 'contenu': main.REPONSE_REPLI}]

    corps = client.post('/message', json={'message': 'je ne sais pas', 'historique': historique}).json()

    assert corps['reponse'] == main.REPONSE_REPLI_BIS


# --- Profil de tendance (volet D) ----------------------------------------------

def test_le_profil_de_tendance_est_transmis_au_modele(monkeypatch):
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda message: [])
    monkeypatch.setattr(main, 'generation_disponible', lambda: True)
    recu = {}

    def ecouter_espion(*args, **options):
        recu['profil'] = options['profil']
        return 'Comment se passent vos journées en ce moment ?'

    monkeypatch.setattr(main, 'ecouter', ecouter_espion)
    profil = ['humeur en baisse sur 7 jours', 'journal irrégulier']

    client.post('/message', json={'message': 'bof', 'profil_tendance': profil})

    assert recu['profil'] == profil


def test_le_profil_arrive_au_modele_comme_consigne_de_ton():
    messages = generateur._contexte_profil(['humeur en baisse sur 7 jours'])

    assert messages[0]['role'] == 'system'
    assert 'humeur en baisse sur 7 jours' in messages[0]['content']
    assert 'TON seulement' in messages[0]['content']


def test_sans_profil_aucune_consigne_n_est_ajoutee():
    assert generateur._contexte_profil([]) == []


def test_un_profil_de_tendance_ne_retarde_jamais_une_reponse_d_urgence(monkeypatch):
    monkeypatch.setattr(main, 'ecouter', lambda *a, **k: pytest.fail('modèle appelé sur une détresse'))
    monkeypatch.setattr(main, 'generer', lambda *a, **k: pytest.fail('modèle appelé sur une détresse'))

    corps = client.post(
        '/message', json={'message': 'je veux mourir', 'profil_tendance': ['humeur stable sur 7 jours']}
    ).json()

    assert corps['urgence'] is True


def test_un_profil_trop_long_est_refuse():
    reponse = client.post('/message', json={'message': 'bonjour', 'profil_tendance': ['x' * 81]})
    assert reponse.status_code == 422


# --- Recherche replacée dans la conversation -------------------------------------

def test_un_message_sans_sujet_retrouve_la_ressource_grace_a_la_conversation(monkeypatch):
    def rechercher_espion(requete):
        return [RESSOURCE] if 'examen' in requete else []

    monkeypatch.setattr(main, 'rechercher_plusieurs', rechercher_espion)
    historique = [main.EchangePrecedent(auteur='UTILISATEUR', contenu="J'ai un examen dans deux jours")]

    assert main._rechercher_avec_contexte('et je fais comment ?', historique) == [RESSOURCE]


def test_le_message_seul_garde_la_priorite_quand_le_sujet_change(monkeypatch):
    proche = {**RESSOURCE, 'ressource_id': 8, 'titre': 'Dormir mieux', 'similarite': 0.9}
    ancienne = {**RESSOURCE, 'similarite': 0.5}
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda requete: [ancienne, proche] if 'examen' in requete else [proche])
    historique = [main.EchangePrecedent(auteur='UTILISATEUR', contenu="J'ai un examen")]

    trouvees = main._rechercher_avec_contexte('je dors mal', historique)

    assert [r['ressource_id'] for r in trouvees] == [8, 7]


def test_sans_historique_la_recherche_porte_sur_le_message_seul(monkeypatch):
    requetes = []
    monkeypatch.setattr(main, 'rechercher_plusieurs', lambda requete: requetes.append(requete) or [])

    main._rechercher_avec_contexte('bonjour', [])

    assert requetes == ['bonjour']


def test_l_encart_montre_une_ressource_du_catalogue_citee_par_titou():
    catalogue = [{'ressource_id': 12, 'titre': 'Exercice de respiration guidée, 4 minutes', 'thematique': 'Respiration'}]
    texte = "L'exercice de respiration guidée de 4 minutes de la bibliothèque peut vous apaiser."

    assert main.ressource_evoquee(texte, [AUTRE], catalogue)['ressource_id'] == 12


def test_un_titre_d_un_seul_mot_ne_suffit_pas_a_choisir_l_encart():
    catalogue = [{'ressource_id': 13, 'titre': 'Respirer', 'thematique': 'Respiration'}]
    assert main.ressource_evoquee('Prenez le temps de respirer un peu.', [], catalogue) is None
