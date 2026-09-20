from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response

from apps.comptes.permissions import EstAdministrateur, EstUtilisateur

from .models import CommentaireForum, PublicationForum, StatutModeration
from .serializers import (
    CommentaireForumEcritureSerializer,
    CommentaireForumModerationSerializer,
    ModerationSerializer,
    PublicationForumDetailSerializer,
    PublicationForumEcritureSerializer,
    PublicationForumLectureSerializer,
    PublicationForumModerationSerializer,
)


class PublicationForumListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/forum/publications — modération avant publication.

    Filtres : ?thematique=STRESS et ?q=texte (titre ou contenu).
    """

    permission_classes = [EstUtilisateur]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PublicationForumEcritureSerializer
        return PublicationForumLectureSerializer

    def get_queryset(self):
        # Seules les publications VISIBLE sont proposées : la modération est
        # a priori, rien n'est visible avant validation par un administrateur.
        queryset = PublicationForum.objects.filter(
            statut_moderation=StatutModeration.VISIBLE
        ).select_related('utilisateur')

        thematique = self.request.query_params.get('thematique')
        if thematique:
            queryset = queryset.filter(thematique=thematique)

        recherche = self.request.query_params.get('q')
        if recherche:
            queryset = queryset.filter(Q(titre__icontains=recherche) | Q(contenu__icontains=recherche))

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': "Votre publication a été envoyée. Elle sera visible après relecture par un modérateur."},
            status=201,
        )


class PublicationForumDetailView(generics.RetrieveAPIView):
    """GET /api/forum/publications/{id} — avec ses commentaires visibles."""

    permission_classes = [EstUtilisateur]
    serializer_class = PublicationForumDetailSerializer

    def get_queryset(self):
        return PublicationForum.objects.filter(
            statut_moderation=StatutModeration.VISIBLE
        ).select_related('utilisateur')


class CommentaireForumCreateView(generics.CreateAPIView):
    """POST /api/forum/publications/{id}/commentaires"""

    permission_classes = [EstUtilisateur]
    serializer_class = CommentaireForumEcritureSerializer

    def get_serializer_context(self):
        contexte = super().get_serializer_context()
        contexte['publication'] = get_object_or_404(
            PublicationForum, pk=self.kwargs['pk'], statut_moderation=StatutModeration.VISIBLE
        )
        return contexte

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': "Votre message a été envoyé. Il sera visible après relecture par un modérateur."},
            status=201,
        )


# --- Modération (écran d'administration) ------------------------------------


class PublicationForumModerationListView(generics.ListAPIView):
    """GET /api/forum/moderation/publications?statut=EN_ATTENTE — toutes, réservé à l'administration."""

    permission_classes = [EstAdministrateur]
    serializer_class = PublicationForumModerationSerializer

    def get_queryset(self):
        queryset = PublicationForum.objects.select_related('utilisateur').all()
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut_moderation=statut)
        return queryset


class PublicationForumModerationDetailView(generics.UpdateAPIView):
    """PATCH /api/forum/moderation/publications/{id} — change le statut de modération."""

    permission_classes = [EstAdministrateur]
    serializer_class = ModerationSerializer
    http_method_names = ['patch']
    queryset = PublicationForum.objects.all()


class CommentaireForumModerationListView(generics.ListAPIView):
    """GET /api/forum/moderation/commentaires?statut=EN_ATTENTE — tous, réservé à l'administration."""

    permission_classes = [EstAdministrateur]
    serializer_class = CommentaireForumModerationSerializer

    def get_queryset(self):
        queryset = CommentaireForum.objects.select_related('utilisateur', 'publication').all()
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut_moderation=statut)
        return queryset


class CommentaireForumModerationDetailView(generics.UpdateAPIView):
    """PATCH /api/forum/moderation/commentaires/{id} — change le statut de modération."""

    permission_classes = [EstAdministrateur]
    serializer_class = ModerationSerializer
    http_method_names = ['patch']
    queryset = CommentaireForum.objects.all()
