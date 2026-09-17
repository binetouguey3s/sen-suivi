from django.contrib import admin

from .models import AutoEvaluation, SuiviHumeur


@admin.register(SuiviHumeur)
class SuiviHumeurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date', 'score_humeur')
    list_filter = ('score_humeur',)
    date_hierarchy = 'date'


@admin.register(AutoEvaluation)
class AutoEvaluationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_evaluation', 'score_de_tendance', 'date')
    list_filter = ('type_evaluation',)
