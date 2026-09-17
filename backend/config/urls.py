"""Routes du back-end Sen Suivi.

POST /api/chatbot/message n'est pas encore branché : il dépend du
microservice IA, ajouté à l'étape 4 avec le chatbot lui-même.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.comptes.urls')),
    path('api/', include('apps.suivi.urls')),
    path('api/', include('apps.ressources.urls')),
    path('api/', include('apps.relations.urls')),
    path('api/', include('apps.forum.urls')),
]
