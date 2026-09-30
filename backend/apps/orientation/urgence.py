"""Jeton d'urgence : gratuité de la mise en relation pour une personne en détresse.

Quand le chatbot détecte une détresse chez un utilisateur connecté, il lui
remet ce jeton signé et limité dans le temps. Présenté avec une demande de
mise en relation, il supprime tout écran de paiement.

Rien n'est enregistré côté serveur : la détresse d'une personne n'est jamais
stockée, le jeton seul en porte la preuve le temps nécessaire. Il est lié au
compte qui l'a reçu et ne peut pas être fabriqué sans la clé secrète.
"""

from django.conf import settings
from django.core import signing

_SEL = 'sen-suivi.urgence'


def emettre_jeton(utilisateur) -> str:
    return signing.TimestampSigner(salt=_SEL).sign(str(utilisateur.pk))


def jeton_valide(jeton: str | None, utilisateur) -> bool:
    if not jeton or utilisateur is None:
        return False
    try:
        valeur = signing.TimestampSigner(salt=_SEL).unsign(jeton, max_age=settings.URGENCE_JETON_HEURES * 3600)
    except signing.BadSignature:
        return False
    return valeur == str(utilisateur.pk)


def en_detresse(request) -> bool:
    """Jeton envoyé par le front dans l'en-tête X-Jeton-Urgence."""
    utilisateur = getattr(request.user, 'utilisateur', None) if request.user.is_authenticated else None
    return jeton_valide(request.headers.get('X-Jeton-Urgence'), utilisateur)
