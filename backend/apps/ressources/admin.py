from django.contrib import admin, messages

from .models import Favori, LieuDetente, Ressource


@admin.register(Ressource)
class RessourceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_ressource', 'thematique', 'url_audio')
    list_filter = ('type_ressource', 'thematique')
    search_fields = ('titre', 'thematique')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.podcast_sans_audio:
            # Autorisé, mais à signaler : la page ne pourra lire que le résumé
            messages.warning(
                request,
                f"« {obj.titre} » est un podcast sans fichier audio : la page proposera seulement "
                "d'écouter le résumé avec la voix du navigateur. Ajoutez un fichier, ou lancez "
                "« python manage.py generer_audio_podcasts ».",
            )


@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'ressource', 'date_ajout')


class FiltrePhotoEnvoyee(admin.SimpleListFilter):
    """Photos envoyées seulement : celles livrées avec le front-end ne sont pas en base."""

    title = 'photo envoyée'
    parameter_name = 'photo'

    def lookups(self, request, model_admin):
        return (('oui', 'Oui'), ('non', 'Non'))

    def queryset(self, request, queryset):
        if self.value() == 'oui':
            return queryset.exclude(image='')
        if self.value() == 'non':
            return queryset.filter(image='')
        return queryset


@admin.register(LieuDetente)
class LieuDetenteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'ville', 'categorie', 'acces')
    list_filter = ('region', 'categorie', 'acces', FiltrePhotoEnvoyee)
    search_fields = ('nom', 'ville', 'type_lieu')
