from django.urls import path

from . import views

urlpatterns = [
    path('forum/publications', views.PublicationForumListCreateView.as_view()),
    path('forum/publications/<int:pk>', views.PublicationForumDetailView.as_view()),
    path('forum/publications/<int:pk>/commentaires', views.CommentaireForumCreateView.as_view()),
    path('forum/moderation/publications', views.PublicationForumModerationListView.as_view()),
    path('forum/moderation/publications/<int:pk>', views.PublicationForumModerationDetailView.as_view()),
    path('forum/moderation/commentaires', views.CommentaireForumModerationListView.as_view()),
    path('forum/moderation/commentaires/<int:pk>', views.CommentaireForumModerationDetailView.as_view()),
]
