from django.urls import path

from . import views

urlpatterns = [
    path('ressources', views.RessourceListView.as_view()),
    path('ressources/<int:pk>', views.RessourceDetailView.as_view()),
    path('ressources/<int:pk>/publier', views.RessourcePublierView.as_view()),
    path('ressources/<int:pk>/refuser', views.RessourceRefuserView.as_view()),
    path('pro/ressources', views.ProRessourceListCreateView.as_view()),
    path('pro/ressources/<int:pk>', views.ProRessourceDetailView.as_view()),
    path('pro/ressources/<int:pk>/soumettre', views.ProRessourceSoumettreView.as_view()),
    path('lieux', views.LieuDetenteListView.as_view()),
    path('lieux/<int:pk>', views.LieuDetenteDetailView.as_view()),
    path('favoris', views.FavoriListCreateView.as_view()),
    path('favoris/<int:ressource_id>', views.FavoriSuppressionView.as_view()),
]
