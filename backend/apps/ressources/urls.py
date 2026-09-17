from django.urls import path

from . import views

urlpatterns = [
    path('ressources', views.RessourceListView.as_view()),
    path('lieux', views.LieuDetenteListView.as_view()),
]
