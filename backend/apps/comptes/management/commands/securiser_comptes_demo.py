"""Sécurise les comptes de démonstration créés par seed_donnees avant
l'ouverture au public : leur mot de passe connu ne doit plus ouvrir de session.

Par défaut, chaque compte reçoit un mot de passe aléatoire que personne ne
connaît : les profils de démonstration restent visibles (annuaire, forum,
ressources), mais plus personne ne peut s'y connecter.
Avec --desactiver, les comptes sont en plus désactivés et disparaissent.

Seuls les comptes en @sensuivi.sn qui ont encore le mot de passe de
démonstration sont concernés : un vrai compte n'est jamais touché.

Usage : python manage.py securiser_comptes_demo [--desactiver]
"""

import secrets

from django.core.management.base import BaseCommand

from apps.comptes.management.commands.seed_donnees import MOT_DE_PASSE_DEMO
from apps.comptes.models import CompteUtilisateur


class Command(BaseCommand):
    help = 'Retire le mot de passe connu des comptes de démonstration (et les désactive avec --desactiver).'

    def add_arguments(self, parser):
        parser.add_argument('--desactiver', action='store_true', help='Désactive aussi les comptes.')

    def handle(self, *args, desactiver=False, **options):
        comptes = [
            c for c in CompteUtilisateur.objects.filter(email__iendswith='@sensuivi.sn')
            if c.check_password(MOT_DE_PASSE_DEMO)
        ]
        for compte in comptes:
            compte.set_password(secrets.token_urlsafe(32))
            if desactiver:
                compte.is_active = False
            compte.save()
            self.stdout.write(f'  {compte.email}')
        action = 'sécurisé(s) et désactivé(s)' if desactiver else 'sécurisé(s)'
        self.stdout.write(self.style.SUCCESS(f'{len(comptes)} compte(s) de démonstration {action}.'))
