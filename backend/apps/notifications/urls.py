from django.urls import path

from . import interne, views

urlpatterns = [
    path('notifications', views.NotificationListView.as_view()),
    path('notifications/tout-lire', views.NotificationToutLireView.as_view()),
    # Réservés à n8n (clé interne), jamais appelés par le front-end
    path('interne/utilisateurs-inactifs', interne.UtilisateursInactifsView.as_view()),
    path('interne/administrateurs', interne.AdministrateursView.as_view()),
    path('interne/notifications-email', interne.CreerNotificationView.as_view()),
]
