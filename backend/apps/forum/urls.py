from django.urls import path

from . import views

urlpatterns = [
    path('forum/publications', views.PublicationForumListCreateView.as_view()),
    path('forum/publications/<int:pk>', views.PublicationForumDetailView.as_view()),
    path('forum/publications/<int:pk>/commentaires', views.CommentaireForumCreateView.as_view()),
]
