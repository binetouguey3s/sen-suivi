"""Permissions liées au type de compte (CompteUtilisateur.type_compte).

Ces classes sont réutilisées par les autres apps plutôt que dupliquées,
car elles ne testent qu'une seule chose : le type de compte connecté.
Chaque app garde son propre permissions.py pour ses règles spécifiques
(propriété d'un objet, etc.) mais importe celles-ci quand elle a juste
besoin de savoir « qui est connecté ».
"""

from rest_framework.permissions import BasePermission

from .models import StatutValidationPro


class EstUtilisateur(BasePermission):
    """Autorise uniquement les comptes de type Utilisateur."""

    message = "Cette action est réservée aux utilisateurs."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type_compte == 'utilisateur'
        )


class EstProfessionnelValide(BasePermission):
    """Autorise uniquement les professionnels dont le compte est VALIDE."""

    message = "Cette action est réservée aux professionnels dont le compte est validé."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type_compte == 'professionnel'
            and request.user.professionnel.statut_validation == StatutValidationPro.VALIDE
        )


class EstAdministrateur(BasePermission):
    """Autorise uniquement les comptes de type Administrateur."""

    message = "Cette action est réservée aux administrateurs."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.type_compte == 'administrateur'
        )
