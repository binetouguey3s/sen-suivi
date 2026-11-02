"""Importe les 98 sites du répertoire. Relançable sans créer de doublon."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.ressources.lieux_senegal import ANCIENS_NOMS, LIEUX_SENEGAL
from apps.ressources.models import LieuDetente

# Écrits seulement à la création : une correction faite dans l'administration
# (description, position) n'est pas écrasée par un nouvel import. La photo
# n'est jamais touchée.
CHAMPS_A_LA_CREATION = ('description', 'latitude', 'longitude')


def _reprendre_ancien_lieu(site: dict) -> None:
    """Un lieu d'avant le répertoire n'a pas de région : il prend le nom et la
    région du PDF et garde son identifiant. S'il a été recréé à côté du
    nouveau (ancien seed), il disparaît."""
    ancien_nom = ANCIENS_NOMS.get(site['nom'])
    if ancien_nom is None:
        return
    for ancien in LieuDetente.objects.filter(nom=ancien_nom, region=''):
        if LieuDetente.objects.filter(nom=site['nom'], region=site['region']).exists():
            ancien.delete()
        else:
            ancien.nom, ancien.region = site['nom'], site['region']
            ancien.save(update_fields=['nom', 'region'])


class Command(BaseCommand):
    help = 'Importe ou met à jour les 98 sites du répertoire des lieux de détente du Sénégal.'

    @transaction.atomic
    def handle(self, *args, **options):
        crees = 0
        for site in LIEUX_SENEGAL:
            _reprendre_ancien_lieu(site)
            cle = {champ: site[champ] for champ in ('nom', 'region')}
            colonnes_pdf = {
                champ: valeur for champ, valeur in site.items() if champ not in (*cle, *CHAMPS_A_LA_CREATION)
            }
            _, cree = LieuDetente.objects.update_or_create(
                **cle, defaults=colonnes_pdf, create_defaults=site,
            )
            crees += cree
        self.stdout.write(self.style.SUCCESS(
            f'{len(LIEUX_SENEGAL)} lieux importés : {crees} créés, {len(LIEUX_SENEGAL) - crees} mis à jour.'
        ))
