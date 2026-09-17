from datetime import timedelta

from django.utils import timezone
from rest_framework import generics

from apps.comptes.permissions import EstUtilisateur

from .models import QuestionEvaluation, SuiviHumeur
from .serializers import (
    AutoEvaluationEcritureSerializer,
    QuestionEvaluationSerializer,
    SuiviHumeurSerializer,
)


class SuiviHumeurView(generics.ListCreateAPIView):
    """POST enregistre (ou met à jour) l'entrée du jour ; GET ?periode=7j pour le tableau de bord."""

    permission_classes = [EstUtilisateur]
    serializer_class = SuiviHumeurSerializer

    def get_queryset(self):
        queryset = SuiviHumeur.objects.filter(utilisateur=self.request.user.utilisateur)
        periode = self.request.query_params.get('periode', '7j')
        if periode.endswith('j'):
            try:
                nb_jours = int(periode[:-1])
            except ValueError:
                nb_jours = 7
            depuis = timezone.localdate() - timedelta(days=nb_jours)
            queryset = queryset.filter(date__gte=depuis)
        return queryset


class QuestionsEvaluationView(generics.ListAPIView):
    """GET /api/auto-evaluations/questions/{type_evaluation}"""

    permission_classes = [EstUtilisateur]
    serializer_class = QuestionEvaluationSerializer

    def get_queryset(self):
        return QuestionEvaluation.objects.filter(
            type_evaluation=self.kwargs['type_evaluation']
        ).prefetch_related('options')


class AutoEvaluationView(generics.CreateAPIView):
    """POST /api/auto-evaluations : calcule le score et suggère des professionnels."""

    permission_classes = [EstUtilisateur]
    serializer_class = AutoEvaluationEcritureSerializer
