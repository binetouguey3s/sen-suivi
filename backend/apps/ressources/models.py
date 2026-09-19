"""Ressources : Ressource (bibliothèque), Favori, LieuDetente."""

from django.db import models
from django.utils import timezone


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

    class Meta:
        verbose_name = 'ressource'
        verbose_name_plural = 'ressources'
        ordering = ['titre']

    def __str__(self):
        return self.titre


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
