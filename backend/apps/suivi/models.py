"""Suivi : SuiviHumeur (journal quotidien) et AutoEvaluation."""

from django.db import models


class NiveauHumeur(models.TextChoices):
    TRES_MAL = 'TRES_MAL', 'Très mal'
    MAL = 'MAL', 'Mal'
    NEUTRE = 'NEUTRE', 'Neutre'
    BIEN = 'BIEN', 'Bien'
    TRES_BIEN = 'TRES_BIEN', 'Très bien'


class TypeEvaluation(models.TextChoices):
    STRESS = 'STRESS', 'Stress'
    ANXIETE = 'ANXIETE', 'Anxiété'
    FATIGUE = 'FATIGUE', 'Fatigue'


class SuiviHumeur(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='suivis_humeur',
        verbose_name='utilisateur',
    )
    date = models.DateField('date')
    score_humeur = models.CharField('humeur', max_length=10, choices=NiveauHumeur.choices)
    note = models.TextField('note', blank=True)

    class Meta:
        verbose_name = "suivi d'humeur"
        verbose_name_plural = "suivis d'humeur"
        ordering = ['-date']
        constraints = [
            # Une seule entrée par jour et par utilisateur (docs/SPECIFICATIONS.md
            # section 2) ; une seconde saisie le même jour met à jour l'existante,
            # ce que la vue traduira par un update_or_create.
            models.UniqueConstraint(
                fields=['utilisateur', 'date'],
                name='une_entree_par_jour_et_par_utilisateur',
            )
        ]

    def __str__(self):
        return f'{self.utilisateur} — {self.date} ({self.get_score_humeur_display()})'


class AutoEvaluation(models.Model):
    utilisateur = models.ForeignKey(
        'comptes.Utilisateur',
        on_delete=models.CASCADE,
        related_name='auto_evaluations',
        verbose_name='utilisateur',
    )
    date = models.DateTimeField('date', auto_now_add=True)
    type_evaluation = models.CharField(
        "type d'évaluation", max_length=10, choices=TypeEvaluation.choices
    )
    # Score sur 100 ; docs/SPECIFICATIONS.md section 2 précise qu'il est arrondi
    # à l'entier au calcul. Type FloatField pour rester fidèle au diagramme de
    # classes : l'arrondi est une règle appliquée à l'écriture, pas au schéma.
    score_de_tendance = models.FloatField('score de tendance')

    class Meta:
        verbose_name = 'auto-évaluation'
        verbose_name_plural = 'auto-évaluations'
        ordering = ['-date']

    def __str__(self):
        return f'{self.utilisateur} — {self.get_type_evaluation_display()} ({self.score_de_tendance})'
