"""Ressources : Ressource (bibliothèque), Favori, LieuDetente."""

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# Fichier audio d'un podcast : chemin servi par le front-end (« /audio/podcasts/… »)
# ou adresse https. Jamais d'http en clair ni de chemin relatif ambigu.
PREFIXES_AUDIO = ('/', 'https://')


def valider_url_audio(valeur: str) -> None:
    if valeur and not valeur.startswith(PREFIXES_AUDIO):
        raise ValidationError("Indiquez un chemin qui commence par « / » ou une adresse « https:// ».")


# Fichier audio envoyé : extension, taille, puis signature du contenu (on ne
# se fie pas au nom du fichier ni au type annoncé par le navigateur)
EXTENSIONS_AUDIO = ('.mp3', '.m4a', '.ogg')


def _signature_audio(debut: bytes) -> bool:
    return (
        debut.startswith(b'ID3')  # MP3 avec étiquettes
        or (len(debut) > 1 and debut[0] == 0xFF and debut[1] & 0xE0 == 0xE0)  # trame MP3
        or debut[4:8] == b'ftyp'  # M4A (conteneur MP4)
        or debut.startswith(b'OggS')  # OGG
    )


def valider_fichier_audio(fichier) -> None:
    if Path(fichier.name).suffix.lower() not in EXTENSIONS_AUDIO:
        raise ValidationError('Formats acceptés : MP3, M4A ou OGG.')
    if fichier.size > settings.FICHIER_AUDIO_MAX_OCTETS:
        raise ValidationError(f'Le fichier dépasse {settings.FICHIER_AUDIO_MAX_OCTETS // (1024 * 1024)} Mo.')
    fichier.seek(0)
    debut = fichier.read(12)
    fichier.seek(0)
    if not _signature_audio(debut):
        raise ValidationError("Ce fichier n'est pas un enregistrement audio lisible (MP3, M4A ou OGG).")


class TypeRessource(models.TextChoices):
    ARTICLE = 'ARTICLE', 'Article'
    EXERCICE = 'EXERCICE', 'Exercice'
    PODCAST = 'PODCAST', 'Podcast'


class Ressource(models.Model):
    titre = models.CharField('titre', max_length=200)
    type_ressource = models.CharField(
        'type de ressource', max_length=10, choices=TypeRessource.choices
    )
    contenu = models.TextField('contenu')
    thematique = models.CharField('thématique', max_length=100)
    # Ajoutés suite à la correction du diagramme de classes.
    duree_lecture = models.PositiveSmallIntegerField('durée (minutes)', default=5)
    date_publication = models.DateField('date de publication', default=timezone.localdate)
    # Un podcast sans fichier reste publiable : la page propose alors d'écouter
    # le résumé avec la voix du navigateur
    url_audio = models.CharField(
        'fichier audio',
        max_length=300,
        blank=True,
        validators=[valider_url_audio],
        help_text="Obligatoire pour un podcast : « /audio/podcasts/mon-episode.mp3 » ou une adresse https.",
    )
    # Fichier envoyé depuis le formulaire : prioritaire sur url_audio
    fichier_audio = models.FileField(
        'fichier audio envoyé',
        upload_to='audio/',
        blank=True,
        validators=[valider_fichier_audio],
        help_text='MP3, M4A ou OGG, 20 Mo au plus.',
    )

    class Meta:
        verbose_name = 'ressource'
        verbose_name_plural = 'ressources'
        ordering = ['titre']

    def __str__(self):
        return self.titre

    @property
    def podcast_sans_audio(self) -> bool:
        return self.type_ressource == TypeRessource.PODCAST and not (self.fichier_audio or self.url_audio)


class Favori(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='favoris',
        verbose_name='utilisateur',
    )
    ressource = models.ForeignKey(
        Ressource,
        on_delete=models.CASCADE,
        related_name='favoris',
        verbose_name='ressource',
    )
    date_ajout = models.DateTimeField("date d'ajout", auto_now_add=True)

    class Meta:
        verbose_name = 'favori'
        verbose_name_plural = 'favoris'
        ordering = ['-date_ajout']
        constraints = [
            models.UniqueConstraint(
                fields=['utilisateur', 'ressource'],
                name='favori_unique_par_utilisateur_et_ressource',
            )
        ]

    def __str__(self):
        return f'{self.utilisateur} ♥ {self.ressource}'


class LieuDetente(models.Model):
    nom = models.CharField('nom', max_length=150)
    ville = models.CharField('ville', max_length=100)
    description = models.TextField('description')
    categorie = models.CharField('catégorie', max_length=100)
    # Ajoutés suite à la correction du diagramme de classes.
    latitude = models.FloatField('latitude', null=True, blank=True)
    longitude = models.FloatField('longitude', null=True, blank=True)
    acces_libre = models.BooleanField('accès libre', default=True)

    class Meta:
        verbose_name = 'lieu de détente'
        verbose_name_plural = 'lieux de détente'
        ordering = ['ville', 'nom']

    def __str__(self):
        return f'{self.nom} ({self.ville})'
