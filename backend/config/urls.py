"""Routes du back-end Sen Suivi.

Les routes de l'API (section 5 de CLAUDE.md) seront ajoutées à l'étape suivante.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
