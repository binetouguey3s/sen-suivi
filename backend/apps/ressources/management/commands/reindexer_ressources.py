"""Indexe (ou réindexe) toutes les ressources dans le RAG du microservice IA.

À lancer après un import massif de ressources, ou par le workflow n8n
« indexation RAG » quand une ressource est ajoutée ou
modifiée — pour l'instant, cette commande le fait à la demande.
"""

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.ressources.models import Ressource


class Command(BaseCommand):
    help = "Envoie toutes les ressources au microservice IA pour les indexer dans le RAG."

    def handle(self, *args, **options):
        ressources = list(
            Ressource.objects.values('id', 'titre', 'contenu', 'thematique')
        )
        try:
            reponse = httpx.post(
                f'{settings.AI_SERVICE_URL}/reindexer', json=ressources, timeout=120
            )
            reponse.raise_for_status()
        except httpx.HTTPError as erreur:
            self.stderr.write(self.style.ERROR(f"Le microservice IA n'a pas répondu : {erreur}"))
            return

        nombre = reponse.json().get('ressources_indexees', 0)
        self.stdout.write(self.style.SUCCESS(f'{nombre} ressource(s) indexée(s) dans le RAG.'))
