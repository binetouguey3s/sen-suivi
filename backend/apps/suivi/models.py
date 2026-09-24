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
    # Ajouté suite à la correction du diagramme de classes : facteurs
    # d'influence choisis par l'utilisateur (ex. "Travail,Sommeil"), stockés
    # en une seule chaîne comme le prévoit le diagramme (+String etiquettes).
    etiquettes = models.CharField('étiquettes', max_length=255, blank=True)

    class Meta:
        verbose_name = "suivi d'humeur"
        verbose_name_plural = "suivis d'humeur"
        ordering = ['-date']
        constraints = [
            # Une seule entrée par jour et par utilisateur ; une seconde saisie
            # le même jour met à jour l'existante, ce que la vue traduit par un
            # update_or_create.
            models.UniqueConstraint(
                fields=['utilisateur', 'date'],
                name='une_entree_par_jour_et_par_utilisateur',
            )
        ]

    def __str__(self):
        return f'{self.utilisateur} — {self.date} ({self.get_score_humeur_display()})'


class QuestionEvaluation(models.Model):
    """Question d'auto-évaluation, propre à la plateforme (jamais PHQ-9/GAD-7).

    Modélisée en base (et non en constantes Python) pour deux raisons
    (décision de l'autrice) : pouvoir corriger un libellé depuis l'admin
    sans redéployer, et garder les AutoEvaluation rattachables aux
    questions réellement posées, pour un score vérifiable.
    """

    type_evaluation = models.CharField(
        "type d'évaluation", max_length=10, choices=TypeEvaluation.choices
    )
    libelle = models.CharField('libellé', max_length=255)
    ordre = models.PositiveSmallIntegerField('ordre')

    class Meta:
        verbose_name = "question d'évaluation"
        verbose_name_plural = "questions d'évaluation"
        ordering = ['type_evaluation', 'ordre']

    def __str__(self):
        return f'{self.get_type_evaluation_display()} #{self.ordre} — {self.libelle}'


class OptionReponse(models.Model):
    question = models.ForeignKey(
        QuestionEvaluation,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name='question',
    )
    libelle = models.CharField('libellé', max_length=150)
    valeur = models.PositiveSmallIntegerField('valeur')

    class Meta:
        verbose_name = 'option de réponse'
        verbose_name_plural = 'options de réponse'
        ordering = ['question', 'valeur']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valeur__gte=0) & models.Q(valeur__lte=4),
                name='valeur_option_entre_0_et_4',
            )
        ]

    def __str__(self):
        return f'{self.libelle} ({self.valeur})'


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
    # Score sur 100, arrondi à l'entier au calcul. Type FloatField pour rester
    # fidèle au diagramme de classes : l'arrondi est une règle appliquée à
    # l'écriture, pas au schéma.
    score_de_tendance = models.FloatField('score de tendance')

    class Meta:
        verbose_name = 'auto-évaluation'
        verbose_name_plural = 'auto-évaluations'
        ordering = ['-date']

    def __str__(self):
        return f'{self.utilisateur} — {self.get_type_evaluation_display()} ({self.score_de_tendance})'
