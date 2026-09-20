from django.contrib import admin

from .models import CommentaireForum, PublicationForum


@admin.register(PublicationForum)
class PublicationForumAdmin(admin.ModelAdmin):
    list_display = ('titre', 'utilisateur', 'thematique', 'statut_moderation', 'moderateur', 'date')
    list_filter = ('statut_moderation', 'thematique')


@admin.register(CommentaireForum)
class CommentaireForumAdmin(admin.ModelAdmin):
    list_display = ('publication', 'utilisateur', 'statut_moderation', 'date')
    list_filter = ('statut_moderation',)
