"""Questions de la personne sur ce que Titou sait d'elle (« comment je
m'appelle ? », « que savez-vous de moi ? »).

Titou ne sait que ce que la personne a accepté de partager (préférence
« personnalisation_chatbot ») : son prénom et quelques mots-clés. Sans cet
accord, la réponse est fixe, sans modèle de langage, et explique comment
l'activer. Avec l'accord, le modèle répond à partir du profil reçu ; ces
textes servent alors de repli.
"""

import re
import unicodedata

REPONSE_PROFIL_SANS_CONSENTEMENT = (
    "Je n'utilise pas les informations de votre profil, car la personnalisation n'est pas activée. "
    "Vous pouvez l'activer dans Mon profil › Confidentialité : je pourrai alors vous appeler par votre "
    "prénom et vous proposer des ressources plus adaptées."
)

# Visiteur sans compte : il n'y a pas de profil du tout
REPONSE_PROFIL_VISITEUR = (
    "Je ne sais rien de vous : vous n'êtes pas connecté·e, et nos échanges ne sont pas conservés. "
    "Avec un compte Sen Suivi, vous pourrez choisir de partager votre prénom et vos préférences dans "
    "Mon profil, pour que je vous propose des ressources plus adaptées."
)

_RAPPEL_MON_PROFIL = "Vous pouvez modifier ou effacer ces informations à tout moment dans Mon profil."

# La personne demande son propre prénom
_DEMANDE_PRENOM = re.compile(r"comment je m'appelle|je m'appelle comment|mon prenom|mon nom\b")


def _normaliser(texte: str) -> str:
    texte = texte.replace('’', "'").replace('ʼ', "'")
    return unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii').lower()


def demande_prenom(message: str) -> bool:
    return bool(_DEMANDE_PRENOM.search(_normaliser(message)))


def reponse_profil(prenom: str | None, message: str) -> str:
    """Repli, avec consentement : ce que Titou sait, sans rien réciter."""
    if demande_prenom(message):
        if prenom:
            return f"D'après votre profil, vous vous appelez {prenom}. {_RAPPEL_MON_PROFIL}"
        return (
            "Vous ne m'avez pas indiqué de prénom. Vous pouvez en ajouter un dans Mon profil : "
            "je pourrai alors l'utiliser de temps en temps."
        )
    debut = f"D'après votre profil, vous vous appelez {prenom}. " if prenom else ''
    return (
        f"{debut}Avec votre accord, je tiens compte de ce que vous avez partagé dans Mon profil, comme vos "
        "préoccupations et ce qui vous fait du bien, et de la tendance de votre journal, pour choisir des "
        f"ressources adaptées. {_RAPPEL_MON_PROFIL}"
    )
