"""Sécurise les comptes de démonstration créés par seed_donnees avant
l'ouverture au public : leur mot de passe ne doit plus ouvrir de session.

Par défaut, chaque compte reçoit un mot de passe aléatoire que personne ne
connaît : les profils de démonstration restent visibles (annuaire, forum,
ressources), mais plus personne ne peut s'y connecter.
Avec --desactiver, les comptes sont en plus désactivés et disparaissent.
Avec --sauf, les comptes nommés sont laissés tels quels (ceux d'une démonstration).

Seuls les comptes en @sensuivi.sn, le domaine réservé à la démonstration, sont
concernés : un vrai compte (autre adresse) n'est jamais touché.

Usage : python manage.py securiser_comptes_demo [--desactiver] [--sauf e-mail ...]
"""

import secrets

from django.core.management.base import BaseCommand

from apps.comptes.models import CompteUtilisateur

DOMAINE_DEMO = '@sensuivi.sn'


class Command(BaseCommand):
    help = 'Retire le mot de passe des comptes de démonstration (et les désactive avec --desactiver).'

    def add_arguments(self, parser):
        parser.add_argument('--desactiver', action='store_true', help='Désactive aussi les comptes.')
        parser.add_argument('--sauf', nargs='+', default=[], metavar='EMAIL', help='Comptes à laisser tels quels.')

    def handle(self, *args, desactiver=False, sauf=(), **options):
        gardes = {email.strip().lower() for email in sauf}
        comptes = [
            c for c in CompteUtilisateur.objects.filter(email__iendswith=DOMAINE_DEMO)
            if c.email.lower() not in gardes
        ]
        for compte in comptes:
            compte.set_password(secrets.token_urlsafe(32))
            if desactiver:
                compte.is_active = False
            compte.save()
            self.stdout.write(f'  {compte.email}')
        action = 'sécurisé(s) et désactivé(s)' if desactiver else 'sécurisé(s)'
        self.stdout.write(self.style.SUCCESS(f'{len(comptes)} compte(s) de démonstration {action}.'))
