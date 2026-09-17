from django.contrib import admin

from .models import Favori, LieuDetente, Ressource


@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_ressource', 'thematique')
    list_filter = ('type_ressource', 'thematique')
    search_fields = ('titre', 'thematique')


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'ressource', 'date_ajout')


@admin.register(LieuDetente)
class LieuDetenteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'categorie')
    list_filter = ('ville', 'categorie')
    search_fields = ('nom', 'ville')
