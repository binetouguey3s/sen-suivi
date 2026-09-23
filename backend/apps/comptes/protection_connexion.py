"""Protection contre la force brute sur la connexion (directive de sécurité, section 2C).

Les échecs sont comptés séparément par adresse e-mail et par adresse IP.
Dès que l'un des deux compteurs atteint le seuil, la connexion est bloquée
pour la durée configurée, même avec le bon mot de passe.

Les compteurs vivent dans le cache Django (table PostgreSQL, voir CACHES
dans settings.py) : ils sont partagés entre tous les processus du serveur
et survivent à un redémarrage. L'e-mail est haché avant d'être utilisé
comme clé, pour ne jamais stocker d'adresse en clair dans le cache.
"""

import hashlib

from django.conf import settings
from django.core.cache import cache


def _cle(nature, valeur):
    empreinte = hashlib.sha256(valeur.strip().lower().encode()).hexdigest()
    return f'connexion:echecs:{nature}:{empreinte}'


def _cles(email, ip):
    cles = []
    if email:
        cles.append(_cle('email', email))
    if ip:
        cles.append(_cle('ip', ip))
    return cles


def adresse_ip(request):
    """Adresse de la connexion réseau.

    L'en-tête X-Forwarded-For est volontairement ignoré : n'importe quel
    client peut l'écrire, et il suffirait de le changer à chaque essai
    pour échapper au blocage par IP.
    """
    return request.META.get('REMOTE_ADDR', '')


def est_bloque(email, ip):
    seuil = settings.CONNEXION_TENTATIVES_MAX
    return any(cache.get(cle, 0) >= seuil for cle in _cles(email, ip))


def enregistrer_echec(email, ip):
    """Ajoute un échec aux deux compteurs.

    Chaque échec relance le délai : le blocage dure donc
    CONNEXION_BLOCAGE_MINUTES après la dernière tentative ratée.
    """
    duree = settings.CONNEXION_BLOCAGE_MINUTES * 60
    for cle in _cles(email, ip):
        cache.set(cle, cache.get(cle, 0) + 1, timeout=duree)


def reinitialiser(email):
    """Efface le compteur de l'e-mail après une connexion réussie.

    Le compteur de l'IP n'est pas remis à zéro : sinon un attaquant qui
    possède un compte pourrait s'y connecter entre deux essais pour
    effacer ses échecs sur les comptes des autres.
    """
    if email:
        cache.delete(_cle('email', email))
