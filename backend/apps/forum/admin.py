from django.contrib import admin

from .models import PublicationForum


@admin.register(PublicationForum)
class PublicationForumAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'statut_moderation', 'moderateur', 'date')
    list_filter = ('statut_moderation',)
