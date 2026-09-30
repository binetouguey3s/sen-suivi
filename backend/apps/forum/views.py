from datetime import timedelta

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.permissions import EstAdministrateur, EstUtilisateur

from . import moderation as moderation_service
from .models import DECISIONS_BLOQUANTES, CommentaireForum, ModerationMessage, PublicationForum, StatutModeration
from .serializers import (
    CommentaireForumEcritureSerializer,
    CommentaireForumModerationSerializer,
    ContestationSerializer,
    DecisionAdministrateurSerializer,
    FileModerationSerializer,
    ModerationSerializer,
    MonMessageSerializer,
    PublicationForumDetailSerializer,
    PublicationForumEcritureSerializer,
    PublicationForumLectureSerializer,
    PublicationForumModerationSerializer,
    mon_message,
)

MESSAGE_VERIFICATION = "Votre message est en cours de vérification. Il apparaîtra dans quelques secondes s'il respecte la charte."


def _verifier_suspension(request):
    utilisateur = request.user.utilisateur
    # Relu en base : une suspension peut avoir été décidée en arrière-plan
    utilisateur.refresh_from_db(fields=['forum_suspendu_jusqu_au'])
    if moderation_service.est_suspendu(utilisateur):
        fin = timezone.localtime(utilisateur.forum_suspendu_jusqu_au)
        raise PermissionDenied(
            f"Vous pourrez de nouveau publier sur le forum le {fin:%d/%m/%Y}. En attendant, Titou et la "
            "bibliothèque restent à votre écoute."
        )


def _envoye(objet):
    """Enregistré, puis modéré en arrière-plan : l'interface n'attend pas."""
    moderation_service.lancer(objet)
    return Response({'id': objet.pk, 'statut_moderation': objet.statut_moderation, 'detail': MESSAGE_VERIFICATION}, status=201)


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
        _verifier_suspension(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return _envoye(serializer.save())


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
        _verifier_suspension(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return _envoye(serializer.save())


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



# --- Suivi par l'auteur et contestation ---------------------------------------

MES_MESSAGES_JOURS = 30


class MesMessagesView(APIView):
    """GET /api/forum/mes-messages — les messages récents de l'auteur, avec leur
    statut et, s'ils n'ont pas été publiés, l'explication et le droit de contester."""

    permission_classes = [EstUtilisateur]

    def get(self, request):
        utilisateur = request.user.utilisateur
        depuis = timezone.now() - timedelta(days=MES_MESSAGES_JOURS)
        objets = [
            *PublicationForum.objects.filter(utilisateur=utilisateur, date__gte=depuis),
            *CommentaireForum.objects.filter(utilisateur=utilisateur, date__gte=depuis).select_related('publication'),
        ]
        objets.sort(key=lambda o: o.date, reverse=True)
        return Response({
            'suspendu_jusqu_au': utilisateur.forum_suspendu_jusqu_au if moderation_service.est_suspendu(utilisateur) else None,
            'messages': MonMessageSerializer([mon_message(o) for o in objets], many=True).data,
        })


class ContestationView(APIView):
    """POST /api/forum/mes-messages/{publication|commentaire}/{id}/contester — réexamen humain."""

    permission_classes = [EstUtilisateur]

    def post(self, request, type_objet, pk):
        modele = PublicationForum if type_objet == 'publication' else CommentaireForum
        objet = get_object_or_404(modele, pk=pk, utilisateur=request.user.utilisateur)
        moderation = moderation_service.derniere_moderation(objet)
        if objet.statut_moderation != StatutModeration.BLOQUE or moderation is None:
            raise PermissionDenied("Seul un message non publié peut faire l'objet d'un réexamen.")
        if moderation.date_contestation:
            raise PermissionDenied('Un réexamen est déjà en cours pour ce message.')
        serializer = ContestationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        moderation_service.contester(moderation, serializer.validated_data.get('motif', ''))
        return Response({'detail': "Votre demande de réexamen a bien été transmise à l'équipe de Sen Suivi."}, status=201)


# --- File des administrateurs --------------------------------------------------


class FileModerationView(generics.ListAPIView):
    """GET /api/forum/moderation/file — doutes, détresse, blocages graves et
    contestations, du plus au moins prioritaire."""

    permission_classes = [EstAdministrateur]
    serializer_class = FileModerationSerializer
    pagination_class = None

    def get_queryset(self):
        return ModerationMessage.objects.filter(a_traiter=True).select_related(
            'publication__utilisateur', 'commentaire__utilisateur', 'commentaire__publication'
        ).order_by('-priorite', '-date_contestation', 'date')


class DecisionAdministrateurView(APIView):
    """POST /api/forum/moderation/file/{id} — publier, bloquer ou classer, en un clic."""

    permission_classes = [EstAdministrateur]

    def post(self, request, pk):
        moderation = get_object_or_404(ModerationMessage, pk=pk)
        serializer = DecisionAdministrateurSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        moderation_service.trancher(moderation, serializer.validated_data['action'], request.user.administrateur)
        return Response(FileModerationSerializer(moderation).data)


class StatistiquesModerationView(APIView):
    """GET /api/forum/moderation/statistiques — taux de blocage et faux positifs
    sur 30 jours, à partir du journal anonymisé des décisions."""

    permission_classes = [EstAdministrateur]

    def get(self, request):
        depuis = timezone.now() - timedelta(days=30)
        decisions = ModerationMessage.objects.filter(date__gte=depuis)
        total = decisions.count()
        bloques = decisions.filter(decision__in=DECISIONS_BLOQUANTES)
        par_decision = {d['decision']: d['nombre'] for d in decisions.values('decision').annotate(nombre=Count('id'))}
        par_niveau = {d['niveau']: d['nombre'] for d in decisions.values('niveau').annotate(nombre=Count('id'))}
        infirmees = bloques.filter(decision_humaine='PUBLIER').count()
        return Response({
            'total': total,
            'par_decision': par_decision,
            'par_niveau': par_niveau,
            'taux_blocage': round(bloques.count() / total * 100) if total else 0,
            'faux_positifs': infirmees,
            'contestations': decisions.exclude(date_contestation=None).count(),
            'a_traiter': ModerationMessage.objects.filter(a_traiter=True).count(),
        })
