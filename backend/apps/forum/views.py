from rest_framework import generics

from apps.comptes.permissions import EstUtilisateur

from .models import PublicationForum, StatutModeration
from .serializers import PublicationForumEcritureSerializer, PublicationForumLectureSerializer


class PublicationForumListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/forum/publications — modération avant publication."""

    permission_classes = [EstUtilisateur]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PublicationForumEcritureSerializer
        return PublicationForumLectureSerializer

    def get_queryset(self):
        # Seules les publications VISIBLE sont proposées : la modération est
        # a priori, rien n'est visible avant validation par un administrateur.
        return PublicationForum.objects.filter(statut_moderation=StatutModeration.VISIBLE)
