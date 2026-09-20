from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationEmail, NotificationPush, StatutNotification
from .serializers import NotificationLectureSerializer
from .services import OBJET_REINITIALISATION


class NotificationListView(APIView):
    """GET /api/notifications — notifications du compte connecté, les plus récentes d'abord."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = [
            *NotificationEmail.objects.filter(destinataire=request.user).exclude(
                objet=OBJET_REINITIALISATION
            ),
            *NotificationPush.objects.filter(destinataire=request.user),
        ]
        notifications.sort(key=lambda n: n.date_envoi, reverse=True)
        return Response(NotificationLectureSerializer(notifications[:50], many=True).data)


class NotificationToutLireView(APIView):
    """POST /api/notifications/tout-lire"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        for modele in (NotificationEmail, NotificationPush):
            modele.objects.filter(destinataire=request.user).exclude(
                statut=StatutNotification.LUE
            ).update(statut=StatutNotification.LUE)
        return Response({'detail': 'Notifications marquées comme lues.'})
