"""Podcasts : fichier audio exposé par l'API, validé, et généré par synthèse
vocale quand il manque (commande generer_audio_podcasts)."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import httpx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
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


# Débuts de fichiers réels : ce qui est vérifié, c'est le contenu, pas le nom
MP3 = b'ID3\x04\x00\x00\x00\x00\x00\x00' + b'\x00' * 64
M4A = b'\x00\x00\x00\x20ftypM4A ' + b'\x00' * 64
OGG = b'OggS\x00\x02' + b'\x00' * 64


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class FichierAudioTests(APITestCase):
    """L'administration joint directement le fichier audio d'un podcast."""

    def setUp(self):
        from apps.comptes.models import Administrateur, Utilisateur

        self.admin = Administrateur.objects.create(email='admin@test.sn', nom='Admin')
        self.utilisateur = Utilisateur.objects.create(email='awa@test.sn', nom='Diop', prenom='Awa')
        self.ressource = podcast()

    def envoyer(self, nom, contenu, type_mime='audio/mpeg', compte=None):
        self.client.force_authenticate(compte or self.admin)
        fichier = SimpleUploadedFile(nom, contenu, content_type=type_mime)
        return self.client.patch(f'/api/ressources/{self.ressource.pk}', {'fichier_audio': fichier}, format='multipart')

    def test_un_mp3_envoye_est_enregistre_et_expose_par_l_api(self):
        reponse = self.envoyer('episode.mp3', MP3)

        self.assertEqual(reponse.status_code, 200, reponse.data)
        self.ressource.refresh_from_db()
        self.assertTrue(self.ressource.fichier_audio.name.startswith('audio/episode'))
        audio = self.client.get(f'/api/ressources/{self.ressource.pk}').data['audio']
        self.assertTrue(audio.startswith('http://testserver/media/audio/episode'))
        # Le fichier n'est jamais renvoyé tel quel
        self.assertNotIn('fichier_audio', reponse.data)

    def test_m4a_et_ogg_sont_acceptes(self):
        self.assertEqual(self.envoyer('episode.m4a', M4A, 'audio/mp4').status_code, 200)
        self.assertEqual(self.envoyer('episode.ogg', OGG, 'audio/ogg').status_code, 200)

    def test_le_fichier_envoye_passe_devant_url_audio(self):
        self.ressource.url_audio = '/audio/podcasts/ancien.mp3'
        self.ressource.save()
        self.assertEqual(self.client.get(f'/api/ressources/{self.ressource.pk}').data['audio'], '/audio/podcasts/ancien.mp3')

        self.envoyer('nouveau.mp3', MP3)

        self.assertIn('/media/audio/nouveau', self.client.get(f'/api/ressources/{self.ressource.pk}').data['audio'])

    def test_un_mauvais_format_est_refuse(self):
        reponse = self.envoyer('image.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * 64, 'image/png')
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('MP3, M4A ou OGG', str(reponse.data['fichier_audio']))

    def test_un_faux_mp3_est_refuse(self):
        # Bonne extension, mauvais contenu : un document renommé
        reponse = self.envoyer('episode.mp3', b'%PDF-1.7' + b'\x00' * 64)
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('pas un enregistrement audio', str(reponse.data['fichier_audio']))

    @override_settings(FICHIER_AUDIO_MAX_OCTETS=50)
    def test_un_fichier_trop_lourd_est_refuse(self):
        reponse = self.envoyer('episode.mp3', MP3)
        self.assertEqual(reponse.status_code, 400)
        self.assertIn('dépasse', str(reponse.data['fichier_audio']))

    def test_seule_l_administration_peut_envoyer_un_fichier(self):
        self.assertEqual(self.envoyer('episode.mp3', MP3, compte=self.utilisateur).status_code, 403)

    def test_remplacer_ou_retirer_supprime_l_ancien_fichier(self):
        self.envoyer('premier.mp3', MP3)
        self.ressource.refresh_from_db()
        premier = Path(self.ressource.fichier_audio.path)
        self.assertTrue(premier.exists())

        self.envoyer('second.mp3', MP3)
        self.assertFalse(premier.exists())

        self.ressource.refresh_from_db()
        second = Path(self.ressource.fichier_audio.path)
        reponse = self.client.patch(f'/api/ressources/{self.ressource.pk}', {'fichier_audio': None}, format='json')
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(second.exists())
        self.ressource.refresh_from_db()
        self.assertFalse(self.ressource.fichier_audio)

    def test_supprimer_la_ressource_supprime_son_fichier(self):
        self.envoyer('episode.mp3', MP3)
        self.ressource.refresh_from_db()
        fichier = Path(self.ressource.fichier_audio.path)

        self.client.delete(f'/api/ressources/{self.ressource.pk}')

        self.assertFalse(fichier.exists())

    @patch('apps.ressources.audio.httpx.post')
    def test_la_commande_ne_regenere_pas_un_podcast_qui_a_son_fichier(self, post):
        self.envoyer('episode.mp3', MP3)
        post.reset_mock()  # l'envoi a aussi demandé la réindexation (n8n), par le même httpx
        sortie = StringIO()
        call_command('generer_audio_podcasts', '--dossier', tempfile.mkdtemp(), stdout=sortie)
        post.assert_not_called()
