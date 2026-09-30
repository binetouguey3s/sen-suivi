"""Niveau 2b du chatbot : génération encadrée par le modèle de langage.

Deux modes, avec les mêmes garde-fous :
- mode ressources : le modèle répond à partir des seules ressources validées
  trouvées par le RAG (niveau 2a). Il n'invente rien.
- mode écoute : aucune ressource ne correspond (un bonjour, un besoin de
  parler). Le modèle accueille, reformule et pose une question ; il ne donne
  aucun conseil ni aucune information.

Le modèle reçoit aussi les derniers échanges de la conversation, pour suivre
le fil. Sa réponse passe ensuite par le validateur ; si elle est rejetée, ou
si aucun fournisseur ne répond, le chatbot retombe sur la réponse de repli.

Fournisseurs en cascade : tout service compatible avec l'API OpenAI
(/chat/completions) — Groq, Mistral, OpenRouter, Hugging Face, OpenAI… Leur
liste et leur ordre viennent du .env (LLM_FOURNISSEURS) : aucune clé, aucune
adresse, aucun nom de modèle n'est écrit en dur ici.
"""

import logging
import os
import re
import time
from collections.abc import Callable

import httpx

from app.validateur_reponse import reponse_achevee

journal = logging.getLogger(__name__)

_CADRE = """Tu es Titou, l'assistant d'écoute de Sen Suivi, une plateforme sénégalaise de \
prévention et de suivi du bien-être mental. Tu n'es pas un soignant et Sen Suivi ne remplace pas \
un professionnel de santé.

Conversation :
- Tu tiens une vraie conversation : tu tiens compte de tout ce qui a déjà été dit.
- Tu ne te répètes jamais et tu ne reposes jamais une question déjà posée.
- Tu ne termines pas chaque message par une question : si ton message précédent en posait déjà \
une, accueille simplement ce que la personne dit, ou fais une proposition.
- Si la personne te dit que tu poses trop de questions, arrête d'en poser et reste présent.

Ce que Sen Suivi propose, et vers quoi tu peux orienter :
- l'annuaire des professionnels validés (psychologues, sophrologues, coachs en développement \
personnel, coachs sportifs, médiateurs familiaux, assistants sociaux), avec une demande de mise \
en relation depuis leur profil ;
- la bibliothèque de ressources (articles, exercices, podcasts) ;
- le forum, anonyme, pour échanger avec d'autres personnes ;
- le journal d'humeur et les auto-évaluations, pour faire le point ;
- les lieux de détente au Sénégal.
Si la personne demande un spécialiste, oriente-la vers l'annuaire des professionnels de Sen Suivi.

Numéros, chacun pour son usage, et aucun autre :
- 800 805 805 : numéro vert d'écoute, pour parler à quelqu'un maintenant ;
- 1515 : le SAMU, pour une urgence médicale ;
- 18 : les sapeurs-pompiers, seulement en cas de danger physique immédiat.

Ton :
- Vouvoiement obligatoire, tutoiement interdit, même si la personne te tutoie.
- Aucune liste à puces, aucun plan en étapes : tu parles, tu ne rédiges pas une fiche. Un seul \
paragraphe, sans saut de ligne.
- Formules interdites : « je comprends », « je suis désolé pour vous », « c'est normal », \
« courage » ou « bon courage » pour encourager, « restez positif ».
- Ne minimise jamais, ne compare jamais à pire, n'explique jamais à la personne ce qu'elle \
devrait ressentir.

Fond :
- Aucun diagnostic, aucune maladie nommée, aucun médicament, aucune posologie.
- Aucun vocabulaire clinique : ni patient, ni trouble, ni thérapie, ni diagnostic.
- Aucune promesse de guérison ; ne te présente jamais comme un substitut à un professionnel.
- Aucune mention d'abonnement, de formule payante ni de tarif.

Réponds en français, en texte simple, sans mise en forme. Termine toujours ta dernière phrase."""

PROMPT_RESSOURCES = _CADRE + """

Des ressources de Sen Suivi correspondent à ce message. Tu accueilles avant de conseiller, en \
quatre phrases au maximum, une par étape, dans cet ordre :
1. Une phrase qui reformule ce que la personne vit, avec ses mots à elle, sans les répéter mot \
pour mot et sans dramatiser.
2. Une phrase qui normalise sans minimiser : « beaucoup de personnes traversent cela » est \
acceptable, « ce n'est pas grave » ne l'est jamais.
3. UNE SEULE phrase de contenu utile, tirée UNIQUEMENT des ressources fournies. Si la ressource \
décrit plusieurs étapes, résume-les dans cette seule phrase. Si aucune ressource ne correspond \
vraiment à ce que vit la personne, ne la force pas : dis-le simplement.
4. Une question ouverte OU une proposition concrète, jamais les deux (et pas de question si tu \
en as posé une au message précédent).
Si la personne demande un résumé ou des précisions sur une ressource, réponds directement, sans \
reformuler ni normaliser."""

PROMPT_ECOUTE = _CADRE + """

Aucune ressource de Sen Suivi ne correspond précisément à ce message : tu es en mode ÉCOUTE.
- Tu ne donnes aucun conseil ni aucune technique : tu accueilles et tu orientes si besoin.
- Si la personne te salue, salue-la, présente-toi en une phrase comme Titou, et demande-lui \
comment elle se sent aujourd'hui.
- Sinon, reformule avec délicatesse ce qu'elle vit ; ajoute une question ouverte seulement si \
ton message précédent n'en posait pas.
- Si elle demande d'autres ressources, cite des titres du catalogue fourni.
- Si elle demande quelque chose qui sort du bien-être (cuisine, devoirs, actualité…), dis-le \
avec douceur et ramène la conversation vers elle.
- Trois phrases au maximum."""


def _fournisseurs() -> list[dict]:
    """Fournisseurs complets, dans l'ordre de LLM_FOURNISSEURS.

    Pour un préfixe P (par défaut LLM) : P_URL_BASE, P_CLE_API, P_MODELE,
    P_MODELE_SECOURS (facultatif), et l'effort de raisonnement de chacun,
    P_EFFORT_RAISONNEMENT et P_EFFORT_RAISONNEMENT_SECOURS (facultatifs, pour
    les modèles qui « réfléchissent » avant de répondre : chaque modèle
    accepte ses propres valeurs).
    """
    prefixes = [p.strip().upper() for p in os.environ.get('LLM_FOURNISSEURS', 'LLM').split(',') if p.strip()]
    fournisseurs = []
    for prefixe in prefixes:
        url = os.environ.get(f'{prefixe}_URL_BASE', '').rstrip('/')
        cle = os.environ.get(f'{prefixe}_CLE_API', '')
        # (modèle, effort de raisonnement), dans l'ordre d'essai
        modeles = [
            (os.environ.get(f'{prefixe}_{cle_modele}'), os.environ.get(f'{prefixe}_{cle_effort}', ''))
            for cle_modele, cle_effort in (
                ('MODELE', 'EFFORT_RAISONNEMENT'),
                ('MODELE_SECOURS', 'EFFORT_RAISONNEMENT_SECOURS'),
            )
        ]
        modeles = [(modele, effort) for modele, effort in modeles if modele]
        if url and cle and modeles:
            fournisseurs.append({'nom': prefixe, 'url': url, 'cle': cle, 'modeles': modeles})
    return fournisseurs


def _reglages() -> dict:
    return {
        'delai': float(os.environ.get('LLM_DELAI_MAX_SECONDES', '8')),
        'delai_total': float(os.environ.get('LLM_DELAI_TOTAL_SECONDES', '20')),
        'temperature': float(os.environ.get('LLM_TEMPERATURE', '0.3')),
        'max_tokens': int(os.environ.get('LLM_MAX_TOKENS', '300')),
        'historique_max': int(os.environ.get('LLM_HISTORIQUE_MAX', '6')),
    }


def generation_disponible() -> bool:
    return os.environ.get('LLM_ACTIVE', 'false').lower() == 'true' and bool(_fournisseurs())


def _nettoyer_sortie(texte: str) -> str:
    """Retire la réflexion interne que certains modèles écrivent entre balises <think>."""
    return re.sub(r'<think>.*?</think>', '', texte, flags=re.DOTALL).strip()


def _messages_historique(historique: list[dict] | None) -> list[dict]:
    """Derniers échanges, au format du fournisseur ; seul le texte est transmis."""
    reglages = _reglages()
    derniers = (historique or [])[-reglages['historique_max']:] if reglages['historique_max'] > 0 else []
    return [
        {'role': 'user' if e['auteur'] == 'UTILISATEUR' else 'assistant', 'content': e['contenu'][:500]}
        for e in derniers
        # Une réponse de Titou restée inachevée n'est pas transmise : le modèle
        # la recopierait, et la coupure se propagerait de message en message
        if e.get('contenu') and (e['auteur'] == 'UTILISATEUR' or reponse_achevee(e['contenu']))
    ]


def echeance_totale() -> float:
    """Instant limite pour obtenir une réponse, toutes tentatives confondues."""
    return time.monotonic() + _reglages()['delai_total']


def _appeler(
    messages: list[dict], echeance: float | None = None, accepter: Callable[[str], bool] | None = None
) -> str | None:
    """Essaie chaque modèle de chaque fournisseur, dans l'ordre, avant l'échéance :
    Django ne doit jamais attendre plus que son propre délai.

    `accepter` : contrôle appliqué à chaque réponse (le validateur) ; une réponse
    refusée fait passer au modèle suivant plutôt qu'à la réponse de repli.
    """
    reglages = _reglages()
    echeance = echeance if echeance is not None else echeance_totale()
    for fournisseur in _fournisseurs():
        for modele, effort in fournisseur['modeles']:
            restant = echeance - time.monotonic()
            if restant <= 1:
                journal.warning('Budget de temps épuisé avant %s/%s', fournisseur['nom'], modele)
                return None
            corps = {
                'model': modele,
                'messages': messages,
                'temperature': reglages['temperature'],
                'max_tokens': reglages['max_tokens'],
            }
            if effort:
                corps['reasoning_effort'] = effort
            try:
                reponse = httpx.post(
                    f"{fournisseur['url']}/chat/completions",
                    headers={'Authorization': f"Bearer {fournisseur['cle']}"},
                    json=corps,
                    timeout=min(reglages['delai'], restant),
                )
                reponse.raise_for_status()
                choix = reponse.json()['choices'][0]
                # Réponse coupée par la limite de jetons : jamais montrée à moitié
                if choix.get('finish_reason') == 'length':
                    journal.warning('Réponse tronquée de %s/%s', fournisseur['nom'], modele)
                    continue
                texte = _nettoyer_sortie(choix['message']['content'] or '')
                if not texte:
                    journal.warning('Réponse vide de %s/%s', fournisseur['nom'], modele)
                    continue
                # Fin « normale » annoncée, mais phrase coupée : même traitement
                if not reponse_achevee(texte):
                    journal.warning('Réponse inachevée de %s/%s', fournisseur['nom'], modele)
                    continue
                if accepter is None or accepter(texte):
                    return texte
            except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError) as erreur:
                # Jamais le message de l'utilisateur dans les journaux : seulement le type d'erreur
                journal.warning('Modèle %s/%s indisponible : %s', fournisseur['nom'], modele, type(erreur).__name__)
    return None


def _contexte(ressources: list[dict]) -> str:
    blocs = [
        f"Ressource « {r['titre']} » (thématique : {r['thematique']}) :\n{r.get('contenu', '').strip()}"
        for r in ressources
    ]
    return 'Ressources validées de Sen Suivi, seules sources autorisées :\n\n' + '\n\n'.join(blocs)


def _contexte_catalogue(catalogue: list[dict] | None) -> list[dict]:
    """Titres de la bibliothèque, pour citer d'autres ressources si on le demande."""
    if not catalogue:
        return []
    lignes = '\n'.join(f"- « {r['titre']} » ({r['thematique']})" for r in catalogue)
    return [{'role': 'system', 'content': f'Catalogue de la bibliothèque de Sen Suivi (titres seulement) :\n{lignes}'}]


def generer(
    message: str,
    ressources: list[dict],
    historique: list[dict] | None = None,
    catalogue: list[dict] | None = None,
    echeance: float | None = None,
    accepter: Callable[[str], bool] | None = None,
) -> str | None:
    """Mode ressources : réponse tirée des seules ressources fournies, ou None."""
    if not generation_disponible() or not ressources:
        return None
    return _appeler(
        [{'role': 'system', 'content': PROMPT_RESSOURCES}, {'role': 'system', 'content': _contexte(ressources)}]
        + _contexte_catalogue(catalogue)
        + _messages_historique(historique)
        + [{'role': 'user', 'content': message}],
        echeance,
        accepter,
    )


def ecouter(
    message: str,
    historique: list[dict] | None = None,
    catalogue: list[dict] | None = None,
    echeance: float | None = None,
    accepter: Callable[[str], bool] | None = None,
) -> str | None:
    """Mode écoute : accueil, sans aucun conseil, ou None."""
    if not generation_disponible():
        return None
    return _appeler(
        [{'role': 'system', 'content': PROMPT_ECOUTE}]
        + _contexte_catalogue(catalogue)
        + _messages_historique(historique)
        + [{'role': 'user', 'content': message}],
        echeance,
        accepter,
    )
