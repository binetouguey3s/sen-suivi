"""Application des décisions de modération du forum.

Le microservice IA décide (règles, puis modèle) ; ce module applique la
décision, la trace, notifie l'auteur et tient le compteur d'infractions.

Règles absolues :
- rien n'est publié sans contrôle : si le microservice ne répond pas, le
  message attend une validation humaine ;
- une personne en détresse n'est jamais bloquée, et ses messages ne comptent
  jamais comme des infractions ;
- une décision automatique peut toujours être contestée, et un administrateur
  a toujours le dernier mot.
"""

import logging
import threading
from datetime import timedelta

import httpx
from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

from apps.notifications.services import notifier

from .models import (
    DECISIONS_BLOQUANTES,
    CommentaireForum,
    DecisionHumaine,
    DecisionModeration,
    ModerationMessage,
    PublicationForum,
    StatutModeration,
)

journal = logging.getLogger(__name__)

MESSAGE_REPLI = (
    "Votre message est en cours de relecture par l'équipe de Sen Suivi. Il sera publié très vite "
    "s'il respecte la charte du forum."
)


def _texte(objet) -> str:
    if isinstance(objet, PublicationForum):
        return f'{objet.titre}\n{objet.contenu}'
    return objet.contenu


def _analyser(texte: str) -> dict:
    """Décision du microservice ; en cas de panne, attente humaine."""
    try:
        reponse = httpx.post(
            f'{settings.AI_SERVICE_URL}/moderer', json={'texte': texte}, timeout=settings.AI_SERVICE_DELAI_SECONDES
        )
        reponse.raise_for_status()
        return reponse.json()
    except (httpx.HTTPError, ValueError) as erreur:
        journal.warning('Microservice de modération indisponible : %s', type(erreur).__name__)
        return {
            'decision': DecisionModeration.ATTENTE_HUMAINE, 'categorie': 'CONFORME', 'gravite': 0, 'extrait': '',
            'raison': 'service de modération indisponible', 'message': MESSAGE_REPLI, 'niveau': 'REPLI', 'priorite': 1,
        }


def moderer(objet) -> ModerationMessage:
    """Analyse un message EN_ATTENTE, applique la décision et la trace."""
    resultat = _analyser(_texte(objet))
    decision = resultat['decision']
    moderation = ModerationMessage.objects.create(
        publication=objet if isinstance(objet, PublicationForum) else None,
        commentaire=objet if isinstance(objet, CommentaireForum) else None,
        decision=decision,
        categorie=resultat.get('categorie', ''),
        gravite=resultat.get('gravite') or 0,
        raison=(resultat.get('raison') or '')[:255],
        extrait=(resultat.get('extrait') or '')[:500],
        niveau=resultat.get('niveau', ''),
        message_auteur=resultat.get('message') or '',
        priorite=resultat.get('priorite') or 0,
        # File des administrateurs : doutes, détresse et blocages graves
        a_traiter=decision in (
            DecisionModeration.ATTENTE_HUMAINE,
            DecisionModeration.PUBLIER_ACCOMPAGNER,
            DecisionModeration.BLOQUER_PRIORITAIRE,
        ),
    )

    if decision in (DecisionModeration.PUBLIER, DecisionModeration.PUBLIER_ACCOMPAGNER):
        _changer_statut(objet, StatutModeration.VISIBLE)
    elif decision in DECISIONS_BLOQUANTES:
        _changer_statut(objet, StatutModeration.BLOQUE)
    # ATTENTE_HUMAINE : le message reste EN_ATTENTE, invisible, sans blocage définitif

    auteur = objet.utilisateur
    if decision == DecisionModeration.PUBLIER_ACCOMPAGNER or (
        decision == DecisionModeration.ATTENTE_HUMAINE and moderation.priorite >= 2
    ):
        # Message privé avec les numéros d'écoute, dans la cloche de l'auteur
        notifier(auteur, 'Nous sommes là pour vous', moderation.message_auteur)
    elif decision in (DecisionModeration.BLOQUER, DecisionModeration.BLOQUER_PRIORITAIRE):
        notifier(auteur, "Votre message n'a pas été publié", moderation.message_auteur)

    if decision in DECISIONS_BLOQUANTES:
        verifier_suspension(auteur)
    return moderation


def _changer_statut(objet, statut):
    objet.statut_moderation = statut
    objet.save(update_fields=['statut_moderation'])


def lancer(objet):
    """Modération après l'enregistrement, en arrière-plan : l'interface
    n'attend pas le modèle, l'auteur voit son message « en vérification »."""
    classe, pk = type(objet), objet.pk

    def travail():
        try:
            moderer(classe.objects.select_related('utilisateur').get(pk=pk))
        except Exception:  # un échec laisse le message EN_ATTENTE : rien n'est publié sans contrôle
            journal.exception('Modération impossible')
        finally:
            if settings.MODERATION_ASYNCHRONE:
                close_old_connections()

    if settings.MODERATION_ASYNCHRONE:
        transaction.on_commit(lambda: threading.Thread(target=travail, daemon=True).start())
    else:
        transaction.on_commit(travail)


# --- Infractions et suspension ---------------------------------------------------

def infractions(utilisateur) -> int:
    """Blocages maintenus sur la période. Jamais la détresse, jamais une
    décision infirmée par un administrateur."""
    depuis = timezone.now() - timedelta(days=settings.MODERATION_FENETRE_JOURS)
    moderations = ModerationMessage.objects.filter(date__gte=depuis, decision__in=DECISIONS_BLOQUANTES).exclude(
        categorie='DETRESSE'
    ).exclude(decision_humaine=DecisionHumaine.PUBLIER)
    return (
        moderations.filter(publication__utilisateur=utilisateur).count()
        + moderations.filter(commentaire__utilisateur=utilisateur).count()
    )


def verifier_suspension(utilisateur):
    if infractions(utilisateur) < settings.MODERATION_SEUIL_INFRACTIONS:
        return
    fin = timezone.now() + timedelta(days=settings.MODERATION_SUSPENSION_JOURS)
    utilisateur.forum_suspendu_jusqu_au = fin
    utilisateur.save(update_fields=['forum_suspendu_jusqu_au'])
    notifier(
        utilisateur,
        'Pause sur le forum',
        f"Plusieurs de vos messages n'ont pas respecté la charte du forum. Vous pourrez de nouveau publier "
        f"le {timezone.localtime(fin):%d/%m/%Y}. En attendant, Titou, votre journal et la bibliothèque restent "
        "accessibles, et vous pouvez contester une décision depuis le forum.",
    )


def est_suspendu(utilisateur) -> bool:
    fin = utilisateur.forum_suspendu_jusqu_au
    return bool(fin and fin > timezone.now())


# --- Décisions humaines et contestation -----------------------------------------

def trancher(moderation: ModerationMessage, action: str, administrateur) -> ModerationMessage:
    """Décision d'un administrateur, qui l'emporte toujours sur celle de l'IA."""
    objet = moderation.objet
    if action == DecisionHumaine.PUBLIER:
        _changer_statut(objet, StatutModeration.VISIBLE)
        if moderation.decision in DECISIONS_BLOQUANTES or moderation.date_contestation:
            notifier(objet.utilisateur, 'Votre message a été publié', "Après relecture, votre message est visible sur le forum.")
        # Une infraction infirmée ne compte plus : on lève une suspension devenue injustifiée
        utilisateur = objet.utilisateur
        moderation.decision_humaine = action
        moderation.save(update_fields=['decision_humaine'])
        if est_suspendu(utilisateur) and infractions(utilisateur) < settings.MODERATION_SEUIL_INFRACTIONS:
            utilisateur.forum_suspendu_jusqu_au = None
            utilisateur.save(update_fields=['forum_suspendu_jusqu_au'])
    elif action == DecisionHumaine.BLOQUER:
        _changer_statut(objet, StatutModeration.BLOQUE)
    moderation.decision_humaine = action
    moderation.moderateur = administrateur
    moderation.date_traitement = timezone.now()
    moderation.a_traiter = False
    moderation.save(update_fields=['decision_humaine', 'moderateur', 'date_traitement', 'a_traiter'])
    return moderation


def contester(moderation: ModerationMessage, motif: str) -> ModerationMessage:
    """Droit de contestation : l'auteur demande un réexamen humain."""
    moderation.motif_contestation = motif
    moderation.date_contestation = timezone.now()
    moderation.a_traiter = True
    moderation.priorite = max(moderation.priorite, 1)
    moderation.save(update_fields=['motif_contestation', 'date_contestation', 'a_traiter', 'priorite'])
    return moderation


def derniere_moderation(objet) -> ModerationMessage | None:
    return objet.moderations.order_by('-date', '-id').first()
