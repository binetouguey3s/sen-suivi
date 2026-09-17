"""Comptes : CompteUtilisateur (base commune) et ses trois sous-types.

CompteUtilisateur est «abstract» dans le diagramme de classes, mais Django
exige qu'un AUTH_USER_MODEL soit une table concrète (il doit pouvoir être
référencé par clé étrangère ailleurs dans le projet). On utilise donc
l'héritage multi-table : CompteUtilisateur reste la table de référence, et
Utilisateur, Professionnel, Administrateur ont chacun leur propre table,
liée à celle de CompteUtilisateur par une relation un-à-un automatique.
Aucun profil séparé du modèle User natif de Django n'est utilisé :
CompteUtilisateur EST le modèle d'authentification.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class CompteUtilisateurManager(BaseUserManager):
    """Gestionnaire requis par AbstractBaseUser : l'email sert d'identifiant."""

    def create_user(self, email, nom, password=None, **extra_champs):
        if not email:
            raise ValueError("L'email est obligatoire.")
        email = self.normalize_email(email)
        compte = self.model(email=email, nom=nom, **extra_champs)
        compte.set_password(password)
        compte.save(using=self._db)
        return compte

    def create_superuser(self, email, nom, password=None, **extra_champs):
        extra_champs.setdefault('is_staff', True)
        extra_champs.setdefault('is_superuser', True)
        return self.create_user(email, nom, password, **extra_champs)


class StatutValidationPro(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDE = 'VALIDE', 'Validé'
    REFUSE = 'REFUSE', 'Refusé'


class SpecialitePro(models.TextChoices):
    """Les six spécialités autorisées (CLAUDE.md section 4).

    Le diagramme de classes type ce champ en simple string ; cette énumération
    ajoute la contrainte métier explicite : exactement ces six valeurs, pas
    d'autres.
    """

    PSYCHOLOGUE = 'PSYCHOLOGUE', 'Psychologue'
    ASSISTANT_SOCIAL = 'ASSISTANT_SOCIAL', 'Assistant social'
    COACH_DEVELOPPEMENT = 'COACH_DEVELOPPEMENT', 'Coach en développement personnel'
    SOPHROLOGUE = 'SOPHROLOGUE', 'Sophrologue'
    MEDIATEUR_FAMILIAL = 'MEDIATEUR_FAMILIAL', 'Médiateur familial'
    COACH_SPORTIF = 'COACH_SPORTIF', 'Coach sportif'


class CompteUtilisateur(AbstractBaseUser, PermissionsMixin):
    """Base commune à tous les comptes (Utilisateur, Professionnel, Administrateur)."""

    nom = models.CharField('nom', max_length=150)
    email = models.EmailField('email', unique=True)
    # Django nomme ce champ "password" dans tout son framework d'authentification
    # (AbstractBaseUser, formulaires, admin, djangorestframework-simplejwt...).
    # Le renommer en "motDePasse" casserait ces mécanismes : dérogation assumée
    # au principe des noms de champs en français, imposée par le framework,
    # pas par choix de conception.
    date_creation = models.DateTimeField('date de création', auto_now_add=True)

    is_active = models.BooleanField('actif', default=True)
    is_staff = models.BooleanField('accès admin Django', default=False)

    objects = CompteUtilisateurManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom']

    class Meta:
        verbose_name = 'compte utilisateur'
        verbose_name_plural = 'comptes utilisateurs'
        ordering = ['nom']

    def __str__(self):
        return f'{self.nom} ({self.email})'

    @property
    def type_compte(self):
        """Type concret du compte, déduit de la sous-classe présente.

        Calculé à la volée (jamais stocké) pour éviter toute désynchronisation
        avec la table réellement peuplée. Utilisé pour les permissions DRF et
        comme claim JWT à l'étape suivante.
        """
        if hasattr(self, 'administrateur'):
            return 'administrateur'
        if hasattr(self, 'professionnel'):
            return 'professionnel'
        if hasattr(self, 'utilisateur'):
            return 'utilisateur'
        return None


class Utilisateur(CompteUtilisateur):
    prenom = models.CharField('prénom', max_length=150)

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f'{self.prenom} {self.nom}'


class Professionnel(CompteUtilisateur):
    specialite = models.CharField('spécialité', max_length=32, choices=SpecialitePro.choices)
    ville = models.CharField('ville', max_length=100)
    langue = models.CharField('langue', max_length=100)
    tarif_indicatif = models.FloatField('tarif indicatif (FCFA)')
    statut_validation = models.CharField(
        'statut de validation',
        max_length=12,
        choices=StatutValidationPro.choices,
        default=StatutValidationPro.EN_ATTENTE,
    )

    class Meta:
        verbose_name = 'professionnel'
        verbose_name_plural = 'professionnels'
        ordering = ['ville', 'nom']

    def __str__(self):
        return f'{self.nom} — {self.get_specialite_display()}'


class Administrateur(CompteUtilisateur):
    class Meta:
        verbose_name = 'administrateur'
        verbose_name_plural = 'administrateurs'
        ordering = ['nom']

    def __str__(self):
        return f'{self.nom} (administrateur)'
