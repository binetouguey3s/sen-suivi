from django.urls import path

from . import views

urlpatterns = [
    path('suivi-humeur', views.SuiviHumeurView.as_view()),
    path(
        'auto-evaluations/questions/<str:type_evaluation>',
        views.QuestionsEvaluationView.as_view(),
    ),
    path('auto-evaluations', views.AutoEvaluationView.as_view()),
]
