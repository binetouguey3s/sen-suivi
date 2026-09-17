from django.contrib import admin

from .models import NotificationEmail, NotificationPush


@admin.register(NotificationEmail)
class NotificationEmailAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'adresse_email', 'objet', 'statut', 'date_envoi')
    list_filter = ('statut',)


@admin.register(NotificationPush)
class NotificationPushAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'device_token', 'statut', 'date_envoi')
    list_filter = ('statut',)
