from django.contrib import admin

from .models import ConversationChatbot, MessageChatbot


class MessageChatbotInline(admin.TabularInline):
    model = MessageChatbot
    extra = 0


@admin.register(ConversationChatbot)
class ConversationChatbotAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'date', 'consentement_conservation')
    list_filter = ('consentement_conservation',)
    inlines = [MessageChatbotInline]


@admin.register(MessageChatbot)
class MessageChatbotAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'type_expediteur', 'source_reponse', 'date_envoi')
    list_filter = ('type_expediteur', 'source_reponse')
