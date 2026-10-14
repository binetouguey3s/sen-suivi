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


@admin.register(LieuDetente)
class LieuDetenteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'categorie')
    list_filter = ('ville', 'categorie')
    search_fields = ('nom', 'ville')
