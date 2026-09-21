from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import AllowAny

from apps.comptes.permissions import EstAdministrateur, EstUtilisateur
from apps.notifications.services import declencher_workflow

from .models import Favori, LieuDetente, Ressource
from .serializers import FavoriEcritureSerializer, LieuDetenteSerializer, RessourceSerializer


class RessourceListView(generics.ListCreateAPIView):
    """GET /api/ressources — filtres thématique, format et recherche, accès public.
    POST — création réservée à l'administration (Gestion des ressources)."""

    serializer_class = RessourceSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EstAdministrateur()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save()
        declencher_workflow('ressource-modifiee')  # réindexation RAG (n8n)

    def get_queryset(self):
        queryset = Ressource.objects.all()
        thematique = self.request.query_params.get('thematique')
        type_ressource = self.request.query_params.get('format')
        recherche = self.request.query_params.get('q')
        if thematique:
            queryset = queryset.filter(thematique=thematique)
        if type_ressource:
            queryset = queryset.filter(type_ressource=type_ressource)
        if recherche:
            queryset = queryset.filter(
                Q(titre__icontains=recherche)
                | Q(thematique__icontains=recherche)
                | Q(contenu__icontains=recherche)
            )
        return queryset


class RessourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET /api/ressources/{id}, accès public.
    PATCH/DELETE — réservés à l'administration (Gestion des ressources)."""

    serializer_class = RessourceSerializer
    queryset = Ressource.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [EstAdministrateur()]

    def perform_update(self, serializer):
        serializer.save()
        declencher_workflow('ressource-modifiee')  # réindexation RAG (n8n)

    def perform_destroy(self, instance):
        instance.delete()
        declencher_workflow('ressource-modifiee')


class LieuDetenteListView(generics.ListAPIView):
    """GET /api/lieux — filtres ville, catégorie et recherche, accès public."""

    permission_classes = [AllowAny]
    serializer_class = LieuDetenteSerializer

    def get_queryset(self):
        queryset = LieuDetente.objects.all()
        ville = self.request.query_params.get('ville')
        categorie = self.request.query_params.get('categorie')
        recherche = self.request.query_params.get('q')
        if ville:
            queryset = queryset.filter(ville=ville)
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        if recherche:
            queryset = queryset.filter(Q(nom__icontains=recherche) | Q(ville__icontains=recherche))
        return queryset


class LieuDetenteDetailView(generics.RetrieveAPIView):
    """GET /api/lieux/{id}, accès public."""

    permission_classes = [AllowAny]
    serializer_class = LieuDetenteSerializer
    queryset = LieuDetente.objects.all()


class FavoriListCreateView(generics.ListCreateAPIView):
    """GET : identifiants des ressources favorites ; POST : ajoute un favori."""

    permission_classes = [EstUtilisateur]
    serializer_class = FavoriEcritureSerializer

    def get_queryset(self):
        return Favori.objects.filter(utilisateur=self.request.user.utilisateur)


class FavoriSuppressionView(generics.DestroyAPIView):
    """DELETE /api/favoris/{ressource_id}"""

    permission_classes = [EstUtilisateur]

    def get_queryset(self):
        return Favori.objects.filter(utilisateur=self.request.user.utilisateur)

    def get_object(self):
        return generics.get_object_or_404(
            self.get_queryset(), ressource_id=self.kwargs['ressource_id']
        )
