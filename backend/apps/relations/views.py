from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from apps.comptes.permissions import EstProfessionnelValide, EstUtilisateur
from apps.notifications.services import declencher_workflow, notifier

from .models import DemandeContact, MessageRelation, StatutDemandeContact
from .serializers import (
    DemandeContactEcritureSerializer,
    DemandeContactProfessionnelSerializer,
    DemandeContactReponseSerializer,
    DemandeContactUtilisateurSerializer,
    MessageRelationSerializer,
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
        moi = self.request.user.pk
        base = DemandeContact.objects.select_related('utilisateur', 'professionnel').annotate(
            # Messages de l'autre personne que je n'ai pas encore lus
            non_lus=Count('messages', filter=Q(messages__lu_le__isnull=True) & ~Q(messages__auteur_id=moi)),
            dernier_message=Max('messages__date'),
        )
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


class MessagesRelationView(generics.ListCreateAPIView):
    """GET/POST /api/demandes-contact/{id}/messages — messagerie privée.

    Réservée aux deux personnes de la demande, et seulement une fois la
    demande acceptée. Ouvrir la conversation marque comme lus les messages
    de l'autre personne.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MessageRelationSerializer
    pagination_class = None

    def demande(self):
        if not hasattr(self, '_demande'):
            moi = self.request.user.pk
            self._demande = get_object_or_404(
                DemandeContact.objects.select_related('utilisateur', 'professionnel'),
                Q(utilisateur_id=moi) | Q(professionnel_id=moi),
                pk=self.kwargs['pk'],
            )
            if self._demande.statut != StatutDemandeContact.ACCEPTEE:
                raise PermissionDenied("La conversation s'ouvre quand le professionnel accepte la demande.")
        return self._demande

    def get_queryset(self):
        demande = self.demande()
        demande.messages.filter(lu_le__isnull=True).exclude(auteur_id=self.request.user.pk).update(lu_le=timezone.now())
        return demande.messages.all()

    def perform_create(self, serializer):
        demande = self.demande()
        moi = self.request.user
        # Une seule notification tant que l'autre personne n'a pas lu les messages précédents
        deja_en_attente = demande.messages.filter(auteur_id=moi.pk, lu_le__isnull=True).exists()
        serializer.save(demande=demande, auteur=moi)
        if deja_en_attente:
            return
        if moi.pk == demande.utilisateur_id:
            destinataire, expediteur = demande.professionnel, demande.utilisateur.pseudonyme
        else:
            destinataire, expediteur = demande.utilisateur, demande.professionnel.nom
        # Jamais le contenu du message dans la notification : seulement qu'il existe
        notifier(destinataire, 'Nouveau message', f'{expediteur} vous a écrit sur Sen Suivi.')
