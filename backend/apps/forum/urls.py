from django.urls import path

from . import views

urlpatterns = [
    path('forum/publications', views.PublicationForumListCreateView.as_view()),
]
