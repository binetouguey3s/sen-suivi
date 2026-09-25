from rest_framework import generics

from apps.comptes.permissions import EstProfessionnelValide, EstUtilisateur
from apps.notifications.services import declencher_workflow

from .models import DemandeContact
from .serializers import (
    DemandeContactEcritureSerializer,
    DemandeContactProfessionnelSerializer,
    DemandeContactReponseSerializer,
    DemandeContactUtilisateurSerializer,
)


class DemandeContactListCreateView(generics.ListCreateAPIView):
    """POST : un utilisateur crée une demande EN_ATTENTE ; GET : ses demandes (utilisateur)
    ou celles reçues (professionnel validé)."""

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EstUtilisateur()]
        return [(EstUtilisateur | EstProfessionnelValide)()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DemandeContactEcritureSerializer
        if self.request.user.type_compte == 'professionnel':
            return DemandeContactProfessionnelSerializer
        return DemandeContactUtilisateurSerializer

    def perform_create(self, serializer):
        demande = serializer.save()
        # Prévient le professionnel via le workflow n8n (best-effort). Seul le
        # pseudonyme part : l'identité reste masquée jusqu'à l'acceptation.
        declencher_workflow(
            'nouvelle-demande',
            {'professionnel_id': demande.professionnel_id, 'pseudonyme': demande.utilisateur.pseudonyme},
        )

    def get_queryset(self):
        base = DemandeContact.objects.select_related('utilisateur', 'professionnel')
        if self.request.user.type_compte == 'professionnel':
            return base.filter(professionnel=self.request.user.professionnel)
        return base.filter(utilisateur=self.request.user.utilisateur)


class DemandeContactReponseView(generics.UpdateAPIView):
    """PATCH /api/demandes-contact/{id} — le professionnel accepte ou décline."""

    permission_classes = [EstProfessionnelValide]
    serializer_class = DemandeContactReponseSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return DemandeContact.objects.filter(professionnel=self.request.user.professionnel)
