from django.contrib import admin

from .models import AccesMiseEnRelation


@admin.register(AccesMiseEnRelation)
class AccesMiseEnRelationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'moyen', 'statut', 'date_debut', 'date_fin']
    list_filter = ['statut', 'moyen']
    search_fields = ['utilisateur__email', 'reference']
