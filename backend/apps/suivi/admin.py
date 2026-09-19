from django.contrib import admin

from .models import AutoEvaluation, OptionReponse, QuestionEvaluation, SuiviHumeur


@admin.register(SuiviHumeur)
class SuiviHumeurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date', 'score_humeur', 'etiquettes')
    list_filter = ('score_humeur',)
    date_hierarchy = 'date'


@admin.register(AutoEvaluation)
class AutoEvaluationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_evaluation', 'score_de_tendance', 'date')
    list_filter = ('type_evaluation',)


class OptionReponseInline(admin.TabularInline):
    model = OptionReponse
    extra = 4


@admin.register(QuestionEvaluation)
class QuestionEvaluationAdmin(admin.ModelAdmin):
    list_display = ('type_evaluation', 'ordre', 'libelle')
    list_filter = ('type_evaluation',)
    ordering = ('type_evaluation', 'ordre')
    inlines = [OptionReponseInline]
