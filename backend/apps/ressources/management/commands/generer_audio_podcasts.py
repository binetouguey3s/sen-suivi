"""python manage.py generer_audio_podcasts [--dossier …] [--tous]

Pour chaque podcast sans fichier audio, produit un MP3 en lisant le titre puis
le contenu avec la synthèse vocale d'ai-service, l'écrit dans le dossier des
podcasts du front-end (frontend/public/audio/podcasts/) et renseigne url_audio.

Un vrai enregistrement reste préférable : la commande sert de solution de
secours. Si la synthèse n'est pas configurée, rien n'est écrit ni modifié.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.ressources.audio import SyntheseIndisponible, synthetiser, texte_a_lire
from apps.ressources.models import Ressource, TypeRessource

PREFIXE_URL = '/audio/podcasts/'


def nom_de_fichier(ressource: Ressource) -> str:
    """Le fichier déjà prévu (url_audio), sinon un nom tiré du titre."""
    if ressource.url_audio.startswith(PREFIXE_URL):
        return ressource.url_audio.removeprefix(PREFIXE_URL)
    return f"{slugify(ressource.titre).removeprefix('podcast-')}.mp3"


class Command(BaseCommand):
    help = 'Génère par synthèse vocale le MP3 des podcasts qui n’en ont pas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dossier',
            default=settings.PODCASTS_AUDIO_DIR,
            help='Dossier où écrire les MP3 (par défaut : frontend/public/audio/podcasts).',
        )
        parser.add_argument('--tous', action='store_true', help='Régénère aussi les podcasts qui ont déjà un fichier.')

    def handle(self, *args, dossier, tous, **options):
        dossier = Path(dossier)
        a_traiter = []
        for podcast in Ressource.objects.filter(type_ressource=TypeRessource.PODCAST).order_by('pk'):
            if podcast.url_audio.startswith('https://'):
                continue  # fichier hébergé ailleurs : rien à produire
            if not tous and podcast.url_audio and (dossier / nom_de_fichier(podcast)).exists():
                continue
            a_traiter.append(podcast)

        if not a_traiter:
            self.stdout.write(self.style.SUCCESS('Tous les podcasts ont déjà leur fichier audio.'))
            return

        dossier.mkdir(parents=True, exist_ok=True)
        for podcast in a_traiter:
            fichier = nom_de_fichier(podcast)
            try:
                audio = synthetiser(texte_a_lire(podcast.titre, podcast.contenu))
            except SyntheseIndisponible as raison:
                self.stdout.write(self.style.WARNING(
                    f'Synthèse vocale indisponible : {raison}. Aucun fichier écrit pour « {podcast.titre} » '
                    'ni pour les suivants. Vous pouvez aussi déposer un enregistrement MP3 dans '
                    f'{dossier} sous le nom {fichier}.'
                ))
                return
            (dossier / fichier).write_bytes(audio)
            podcast.url_audio = f'{PREFIXE_URL}{fichier}'
            podcast.save(update_fields=['url_audio'])
            self.stdout.write(self.style.SUCCESS(f'« {podcast.titre} » → {dossier / fichier} ({len(audio) // 1024} Ko)'))
