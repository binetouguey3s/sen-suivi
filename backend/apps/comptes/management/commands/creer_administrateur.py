"""Crée un compte administrateur de Sen Suivi (espace d'administration de
l'application et administration Django), avec un mot de passe personnel.

Usage : python manage.py creer_administrateur
"""

from getpass import getpass

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.comptes.models import Administrateur, CompteUtilisateur


class Command(BaseCommand):
    help = "Crée un compte administrateur avec un mot de passe personnel."

    def handle(self, *args, **options):
        email = input('E-mail : ').strip().lower()
        if not email:
            raise CommandError("L'e-mail est obligatoire.")
        if CompteUtilisateur.objects.filter(email=email).exists():
            raise CommandError('Un compte existe déjà avec cet e-mail.')
        nom = input('Nom affiché : ').strip() or 'Administrateur'

        mot_de_passe = getpass('Mot de passe : ')
        if mot_de_passe != getpass('Mot de passe (encore) : '):
            raise CommandError('Les deux mots de passe sont différents.')
        try:
            validate_password(mot_de_passe)
        except ValidationError as erreur:
            raise CommandError(' '.join(erreur.messages)) from erreur

        admin = Administrateur(email=email, nom=nom, is_staff=True, is_superuser=True)
        admin.set_password(mot_de_passe)
        admin.save()
        self.stdout.write(self.style.SUCCESS(f'Administrateur {email} créé.'))
