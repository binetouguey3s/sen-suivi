from rest_framework import generics

from apps.comptes.permissions import EstUtilisateur

from .serializers import DemandeContactEcritureSerializer


class DemandeContactCreateView(generics.CreateAPIView):
    """POST /api/demandes-contact — crée une DemandeContact en EN_ATTENTE."""

    permission_classes = [EstUtilisateur]
    serializer_class = DemandeContactEcritureSerializer
