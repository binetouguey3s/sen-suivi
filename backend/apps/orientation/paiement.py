"""Point d'entrée du paiement mobile money (Wave, Orange Money, Free Money).

Aucun prestataire réel n'est intégré pour l'instant. Le jour où il le sera, il
suffira d'implémenter `PrestatairePaiement` et de le renvoyer depuis
`prestataire_actif()` : la vue et l'interface n'auront pas à changer.
"""


class PrestatairePaiement:
    """Contrat attendu d'un futur prestataire mobile money."""

    def initier(self, acces, telephone: str) -> str:
        """Lance la demande de paiement sur le téléphone ; renvoie la référence."""
        raise NotImplementedError

    def confirmer(self, reference: str) -> bool:
        """Vrai quand le prestataire confirme le paiement (rappel ou vérification)."""
        raise NotImplementedError


def prestataire_actif() -> PrestatairePaiement | None:
    return None
