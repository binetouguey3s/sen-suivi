from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.models import Administrateur
from apps.comptes.permissions import EstAdministrateur, EstProfessionnelValide, EstUtilisateur
from apps.notifications.services import declencher_workflow, notifier

from .models import Favori, LieuDetente, Ressource, StatutRessource
from .serializers import FavoriEcritureSerializer, LieuDetenteSerializer, RessourceProSerializer, RessourceSerializer


def _est_admin(request) -> bool:
    return request.user.is_authenticated and request.user.type_compte == 'administrateur'


def _reindexer():
    # Réindexation RAG (n8n) : seulement quand ce que voit le public change
    declencher_workflow('ressource-modifiee')


class RessourceListView(generics.ListCreateAPIView):
    """GET /api/ressources — filtres thématique, format et recherche, accès public.

    Le public ne voit que les ressources PUBLIEE : c'est cette liste que lit
    l'indexation RAG (n8n), donc Titou ne peut jamais citer un brouillon ni une
    proposition qui n'a pas été validée. L'administration peut demander
    ?statut=TOUS (ou un statut précis) pour la gestion des ressources.
    POST — création réservée à l'administration, publiée directement."""

    serializer_class = RessourceSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [EstAdministrateur()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(statut=StatutRessource.PUBLIEE)
        _reindexer()

    def get_queryset(self):
        queryset = Ressource.objects.select_related('auteur')
        statut = self.request.query_params.get('statut')
        if _est_admin(self.request) and statut:
            if statut != 'TOUS':
                queryset = queryset.filter(statut=statut)
        else:
            queryset = queryset.filter(statut=StatutRessource.PUBLIEE)
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
    """GET /api/ressources/{id}, accès public (ressources PUBLIEE seulement).
    PATCH/DELETE — réservés à l'administration, qui voit tous les statuts."""

    serializer_class = RessourceSerializer

    def get_queryset(self):
        queryset = Ressource.objects.select_related('auteur')
        return queryset if _est_admin(self.request) else queryset.filter(statut=StatutRessource.PUBLIEE)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [EstAdministrateur()]

    def perform_update(self, serializer):
        ressource = serializer.save()
        if ressource.statut == StatutRessource.PUBLIEE:
            _reindexer()

    def perform_destroy(self, instance):
        publiee = instance.statut == StatutRessource.PUBLIEE
        if instance.fichier_audio:
            instance.fichier_audio.delete(save=False)
        instance.delete()
        if publiee:
            _reindexer()


class RessourcePublierView(APIView):
    """POST /api/ressources/{id}/publier — l'administration valide une proposition."""

    permission_classes = [EstAdministrateur]

    def post(self, request, pk):
        ressource = get_object_or_404(Ressource, pk=pk)
        manque = ressource.media_manquant()
        if manque:
            return Response({'detail': manque}, status=status.HTTP_400_BAD_REQUEST)
        ressource.statut = StatutRessource.PUBLIEE
        ressource.motif_refus = ''
        ressource.date_publication = timezone.localdate()
        ressource.save()
        _reindexer()
        if ressource.auteur:
            notifier(
                ressource.auteur,
                f'Votre ressource « {ressource.titre} » est publiée',
                "Elle est maintenant dans la bibliothèque de Sen Suivi, avec votre nom, et Titou peut la recommander.",
            )
        return Response(RessourceSerializer(ressource, context={'request': request}).data)


class MotifRefusSerializer(serializers.Serializer):
    motif = serializers.CharField(min_length=10, max_length=1000, trim_whitespace=True, error_messages={
        'min_length': 'Expliquez le motif en 10 caractères au moins : le professionnel doit savoir quoi corriger.',
    })


class RessourceRefuserView(APIView):
    """POST /api/ressources/{id}/refuser — motif obligatoire, renvoyé au professionnel."""

    permission_classes = [EstAdministrateur]

    def post(self, request, pk):
        ressource = get_object_or_404(Ressource, pk=pk)
        entree = MotifRefusSerializer(data=request.data)
        entree.is_valid(raise_exception=True)
        etait_publiee = ressource.statut == StatutRessource.PUBLIEE
        ressource.statut = StatutRessource.REFUSEE
        ressource.motif_refus = entree.validated_data['motif']
        ressource.save()
        if etait_publiee:
            _reindexer()  # retirée de la bibliothèque
        if ressource.auteur:
            notifier(
                ressource.auteur,
                f'Votre ressource « {ressource.titre} » n’a pas été retenue',
                f'Motif de l’équipe : {ressource.motif_refus} Vous pouvez la corriger depuis « Mes ressources », '
                'puis la soumettre à nouveau.',
            )
        return Response(RessourceSerializer(ressource, context={'request': request}).data)


# ─── Espace professionnel ────────────────────────────────────────────────────

MESSAGE_PUBLIEE = "Pour modifier une ressource publiée ou en cours de relecture, contactez l'administration."
STATUTS_MODIFIABLES = (StatutRessource.BROUILLON, StatutRessource.REFUSEE)


class ProRessourceListCreateView(generics.ListCreateAPIView):
    """GET/POST /api/pro/ressources — ses propres ressources, tous statuts.
    Une ressource créée est un BROUILLON, visible du seul professionnel."""

    permission_classes = [EstProfessionnelValide]
    serializer_class = RessourceProSerializer

    def get_queryset(self):
        return Ressource.objects.filter(auteur=self.request.user.professionnel).select_related('auteur').order_by(
            '-date_modification'
        )

    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user.professionnel, statut=StatutRessource.BROUILLON)


class ProRessourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/pro/ressources/{id} — les siennes seulement ;
    modifiables ou supprimables en BROUILLON ou REFUSEE uniquement."""

    permission_classes = [EstProfessionnelValide]
    serializer_class = RessourceProSerializer

    def get_queryset(self):
        return Ressource.objects.filter(auteur=self.request.user.professionnel).select_related('auteur')

    def _verifier_modifiable(self, ressource):
        if ressource.statut not in STATUTS_MODIFIABLES:
            raise PermissionDenied(MESSAGE_PUBLIEE)

    def perform_update(self, serializer):
        self._verifier_modifiable(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._verifier_modifiable(instance)
        if instance.fichier_audio:
            instance.fichier_audio.delete(save=False)
        instance.delete()


class SoumissionSerializer(serializers.Serializer):
    charte_acceptee = serializers.BooleanField()

    def validate_charte_acceptee(self, valeur):
        if not valeur:
            raise serializers.ValidationError('Cochez l’engagement de la charte pour soumettre.')
        return valeur


TITRE_MIN = 8


class ProRessourceSoumettreView(APIView):
    """POST /api/pro/ressources/{id}/soumettre — BROUILLON ou REFUSEE → EN_ATTENTE,
    charte acceptée ; les administrateurs sont prévenus."""

    permission_classes = [EstProfessionnelValide]

    def post(self, request, pk):
        ressource = get_object_or_404(Ressource, pk=pk, auteur=request.user.professionnel)
        if ressource.statut not in STATUTS_MODIFIABLES:
            return Response({'detail': 'Cette ressource a déjà été soumise.'}, status=status.HTTP_400_BAD_REQUEST)
        SoumissionSerializer(data=request.data).is_valid(raise_exception=True)
        if len(ressource.titre.strip()) < TITRE_MIN:
            return Response({'detail': 'Ajoutez un titre (8 caractères au moins).'}, status=status.HTTP_400_BAD_REQUEST)
        if not ressource.thematique.strip():
            return Response({'detail': 'Choisissez une thématique.'}, status=status.HTTP_400_BAD_REQUEST)
        if not ressource.contenu.strip():
            return Response({'detail': 'Écrivez le contenu de la ressource.'}, status=status.HTTP_400_BAD_REQUEST)
        manque = ressource.media_manquant()
        if manque:
            return Response({'detail': manque}, status=status.HTTP_400_BAD_REQUEST)
        ressource.statut = StatutRessource.EN_ATTENTE
        ressource.date_soumission = timezone.now()
        ressource.save()
        auteur = ressource.auteur
        for administrateur in Administrateur.objects.filter(is_active=True):
            notifier(
                administrateur,
                'Nouvelle ressource à relire',
                f'{auteur.nom} ({auteur.get_specialite_display()}) propose « {ressource.titre} » '
                f'({ressource.get_type_ressource_display().lower()}). À relire dans Gestion des ressources › À valider.',
            )
        return Response(RessourceSerializer(ressource, context={'request': request}).data)


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
