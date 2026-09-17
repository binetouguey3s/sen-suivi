"""Chatbot : ConversationChatbot et MessageChatbot.

Le microservice IA (ai-service/) applique les trois niveaux de traitement
(détection de détresse, classification d'intention, RAG) ; ces modèles ne
font que stocker l'historique validé par ce microservice.
"""

from django.db import models


class TypeExpediteur(models.TextChoices):
    UTILISATEUR = 'UTILISATEUR', 'Utilisateur'
    BOT = 'BOT', 'Bot'


class SourceReponse(models.TextChoices):
    REGLE = 'REGLE', 'Règle'
    RAG = 'RAG', 'RAG'


class ConversationChatbot(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='conversations_chatbot',
        verbose_name='utilisateur',
        null=True,
        blank=True,
        help_text='Vide pour une conversation anonyme : le chatbot est accessible sans compte.',
    )
    date = models.DateTimeField('date', auto_now_add=True)
    # L'historique n'est conservé que si l'utilisateur est connecté ET l'accepte
    # (docs/SPECIFICATIONS.md section 1).
    consentement_conservation = models.BooleanField(
        'consentement à la conservation', default=False
    )

    class Meta:
        verbose_name = 'conversation avec le chatbot'
        verbose_name_plural = 'conversations avec le chatbot'
        ordering = ['-date']

    def __str__(self):
        return f'Conversation du {self.date:%d/%m/%Y %H:%M}'


class MessageChatbot(models.Model):
    conversation = models.ForeignKey(
        ConversationChatbot,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='conversation',
    )
    contenu = models.TextField('contenu')
    type_expediteur = models.CharField(
        "type d'expéditeur", max_length=12, choices=TypeExpediteur.choices
    )
    source_reponse = models.CharField(
        'source de la réponse',
        max_length=6,
        choices=SourceReponse.choices,
        null=True,
        blank=True,
        help_text='Uniquement pour les messages du bot (REGLE pour les niveaux 0 et 1, RAG pour le niveau 2).',
    )
    date_envoi = models.DateTimeField("date d'envoi", auto_now_add=True)

    class Meta:
        verbose_name = 'message du chatbot'
        verbose_name_plural = 'messages du chatbot'
        ordering = ['date_envoi']

    def __str__(self):
        return f'{self.get_type_expediteur_display()} — {self.contenu[:50]}'
