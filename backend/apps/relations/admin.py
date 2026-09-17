from django.contrib import admin

from .models import DemandeContact


@admin.register(DemandeContact)
class DemandeContactAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'professionnel', 'statut', 'date')
    list_filter = ('statut',)
