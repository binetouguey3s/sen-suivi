"""Indexe (ou réindexe) toutes les ressources dans le RAG du microservice IA.

À lancer après un import massif de ressources. Elle est aussi lancée à chaque
démarrage en production (demarrer.sh). Sans n8n, Django réindexe aussi seul
quand une ressource publiée change (apps.notifications.services).
"""

import httpx
from django.core.management.base import BaseCommand

from apps.ressources.indexation import reindexer_rag


class Command(BaseCommand):
    help = "Envoie toutes les ressources au microservice IA pour les indexer dans le RAG."

    def handle(self, *args, **options):
        try:
            nombre = reindexer_rag()
        except httpx.HTTPError as erreur:
            self.stderr.write(self.style.ERROR(f"Le microservice IA n'a pas répondu : {erreur}"))
            return
        self.stdout.write(self.style.SUCCESS(f'{nombre} ressource(s) indexée(s) dans le RAG.'))
