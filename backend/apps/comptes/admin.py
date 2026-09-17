from django.contrib import admin

from .models import Administrateur, CompteUtilisateur, Professionnel, Utilisateur


@admin.register(CompteUtilisateur)
class CompteUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'type_compte', 'date_creation', 'is_active')
    search_fields = ('nom', 'email')


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'pseudonyme', 'date_creation')
    search_fields = ('prenom', 'nom', 'email', 'pseudonyme')
    readonly_fields = ('pseudonyme',)


@admin.register(Professionnel)
class ProfessionnelAdmin(admin.ModelAdmin):
    list_display = ('nom', 'specialite', 'ville', 'statut_validation', 'tarif_indicatif')
    list_filter = ('specialite', 'ville', 'statut_validation')
    search_fields = ('nom', 'ville')


@admin.register(Administrateur)
class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'date_creation')
    search_fields = ('nom', 'email')
