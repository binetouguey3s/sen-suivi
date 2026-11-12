"""Routes du back-end Sen Suivi."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def sante(_request):
    """GET /api/sante — l'hébergeur et la surveillance vérifient que le site répond."""
    return JsonResponse({'statut': 'ok'})


urlpatterns = [
    path('api/sante', sante),
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
# En production, ils sont servis par le stockage externe (STOCKAGE_BUCKET).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
