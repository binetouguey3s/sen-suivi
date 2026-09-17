from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import LieuDetente, Ressource
from .serializers import LieuDetenteSerializer, RessourceSerializer


class RessourceListView(generics.ListAPIView):
    """GET /api/ressources — filtres thématique et format, accès public."""

    permission_classes = [AllowAny]
    serializer_class = RessourceSerializer

    def get_queryset(self):
        queryset = Ressource.objects.all()
        thematique = self.request.query_params.get('thematique')
        type_ressource = self.request.query_params.get('format')
        if thematique:
            queryset = queryset.filter(thematique=thematique)
        if type_ressource:
            queryset = queryset.filter(type_ressource=type_ressource)
        return queryset


class LieuDetenteListView(generics.ListAPIView):
    """GET /api/lieux — filtres ville et catégorie, accès public."""

    permission_classes = [AllowAny]
    serializer_class = LieuDetenteSerializer

    def get_queryset(self):
        queryset = LieuDetente.objects.all()
        ville = self.request.query_params.get('ville')
        categorie = self.request.query_params.get('categorie')
        if ville:
            queryset = queryset.filter(ville=ville)
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        return queryset
