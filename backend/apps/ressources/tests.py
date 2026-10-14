"""Podcasts : fichier audio exposé par l'API, validé, et généré par synthèse
vocale quand il manque (commande generer_audio_podcasts)."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import httpx
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

from .audio import TAILLE_MORCEAU, morceaux, texte_a_lire
from .models import Ressource
from .serializers import RessourceSerializer

CONTENU = """Un épisode pour souffler.

## Au programme

Trois voix, trois histoires.

> Prendre soin de soi, c'est aussi de la teranga."""


def podcast(**champs):
    return Ressource.objects.create(
        titre='Podcast : la teranga commence par soi-même', type_ressource='PODCAST',
        thematique='Bien-être', contenu=CONTENU, **champs,
    )


class UrlAudioTests(APITestCase):
    def test_l_api_expose_le_fichier_audio(self):
        ressource = podcast(url_audio='/audio/podcasts/teranga.mp3')

        corps = self.client.get(f'/api/ressources/{ressource.pk}').data

        self.assertEqual(corps['url_audio'], '/audio/podcasts/teranga.mp3')
        self.assertEqual(self.client.get('/api/ressources').data[0]['url_audio'], '/audio/podcasts/teranga.mp3')

    def test_un_podcast_sans_fichier_reste_autorise(self):
        donnees = {'titre': 'Épisode', 'type_ressource': 'PODCAST', 'contenu': '…', 'thematique': 'Bien-être', 'url_audio': ''}
        self.assertTrue(RessourceSerializer(data=donnees).is_valid())
        self.assertTrue(podcast().podcast_sans_audio)

    def test_seuls_un_chemin_ou_une_adresse_https_sont_acceptes(self):
        donnees = {'titre': 'Épisode', 'type_ressource': 'PODCAST', 'contenu': '…', 'thematique': 'Bien-être'}
        for valide in ('/audio/podcasts/episode.mp3', 'https://exemple.sn/episode.mp3'):
            self.assertTrue(RessourceSerializer(data={**donnees, 'url_audio': valide}).is_valid(), valide)
        for invalide in ('http://exemple.sn/episode.mp3', 'episode.mp3', 'javascript:alert(1)'):
            self.assertFalse(RessourceSerializer(data={**donnees, 'url_audio': invalide}).is_valid(), invalide)


class TexteALireTests(TestCase):
    def test_intertitres_en_pause_et_citations_lues_normalement(self):
        texte = texte_a_lire('Podcast : la teranga commence par soi-même', CONTENU)

        self.assertEqual(texte.split('\n\n'), [
            'Podcast : la teranga commence par soi-même.',
            'Un épisode pour souffler.',
            'Au programme.',
            'Trois voix, trois histoires.',
            "Prendre soin de soi, c'est aussi de la teranga.",
        ])

    def test_le_texte_est_decoupe_sous_la_limite_du_microservice(self):
        long = '\n\n'.join(['Une phrase calme et posée. ' * 40] * 12)

        parties = morceaux(long)

        self.assertGreater(len(parties), 1)
        self.assertTrue(all(len(p) <= TAILLE_MORCEAU for p in parties))
        self.assertEqual(''.join(parties).replace('\n', '').replace(' ', ''), long.replace('\n', '').replace(' ', ''))


class GenererAudioPodcastsTests(TestCase):
    def setUp(self):
        self.dossier = Path(tempfile.mkdtemp())

    def lancer(self, *options):
        sortie = StringIO()
        call_command('generer_audio_podcasts', '--dossier', str(self.dossier), *options, stdout=sortie)
        return sortie.getvalue()

    @patch('apps.ressources.audio.httpx.post')
    def test_la_synthese_ecrit_le_mp3_et_renseigne_url_audio(self, post):
        post.return_value = httpx.Response(200, content=b'ID3-morceau')
        ressource = podcast()
        Ressource.objects.create(titre='Un article', type_ressource='ARTICLE', thematique='Stress', contenu='…')

        sortie = self.lancer()

        ressource.refresh_from_db()
        self.assertEqual(ressource.url_audio, '/audio/podcasts/la-teranga-commence-par-soi-meme.mp3')
        self.assertEqual((self.dossier / 'la-teranga-commence-par-soi-meme.mp3').read_bytes(), b'ID3-morceau')
        self.assertIn('la teranga commence par soi-même', sortie)
        # Seul le podcast est lu, titre compris
        self.assertEqual(post.call_count, 1)
        self.assertTrue(post.call_args.kwargs['json']['texte'].startswith('Podcast : la teranga commence par soi-même.'))

    @patch('apps.ressources.audio.httpx.post')
    def test_le_nom_prevu_dans_url_audio_est_garde(self, post):
        post.return_value = httpx.Response(200, content=b'ID3')
        podcast(url_audio='/audio/podcasts/teranga.mp3')

        self.lancer()

        self.assertTrue((self.dossier / 'teranga.mp3').exists())

    @patch('apps.ressources.audio.httpx.post')
    def test_un_fichier_deja_present_n_est_pas_regenere(self, post):
        podcast(url_audio='/audio/podcasts/teranga.mp3')
        (self.dossier / 'teranga.mp3').write_bytes(b'enregistrement')

        sortie = self.lancer()

        post.assert_not_called()
        self.assertIn('déjà leur fichier', sortie)
        self.assertEqual((self.dossier / 'teranga.mp3').read_bytes(), b'enregistrement')

    @patch('apps.ressources.audio.httpx.post')
    def test_sans_synthese_un_message_clair_et_rien_n_est_casse(self, post):
        post.return_value = httpx.Response(503, json={'detail': 'La synthèse vocale est momentanément indisponible.'})
        ressource = podcast()

        sortie = self.lancer()

        ressource.refresh_from_db()
        self.assertEqual(ressource.url_audio, '')
        self.assertEqual(list(self.dossier.iterdir()), [])
        self.assertIn('Synthèse vocale indisponible', sortie)

    @patch('apps.ressources.audio.httpx.post', side_effect=httpx.ConnectError('refusé'))
    def test_microservice_injoignable(self, post):
        podcast()
        self.assertIn('injoignable', self.lancer())
