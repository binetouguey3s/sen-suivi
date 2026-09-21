"""Routes du back-end Sen Suivi."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.comptes.urls')),
    path('api/', include('apps.suivi.urls')),
    path('api/', include('apps.ressources.urls')),
    path('api/', include('apps.relations.urls')),
    path('api/', include('apps.forum.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.chatbot.urls')),
]
