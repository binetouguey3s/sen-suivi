"""Routes du back-end Sen Suivi."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.comptes.urls')),
    path('api/', include('apps.suivi.urls')),
    path('api/', include('apps.ressources.urls')),
    path('api/', include('apps.relations.urls')),
    path('api/', include('apps.forum.urls')),
    path('api/', include('apps.orientation.urls')),
    path('api/', include('apps.notifications.urls')),
    path('api/', include('apps.chatbot.urls')),
]

# Fichiers envoyés (audio des podcasts), servis par Django en développement.
# En production, un serveur web les sert depuis le volume media_data.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
