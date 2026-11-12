from django.urls import path
from . import views

urlpatterns = [
    path("songs/", views.song_list, name="song_list"),
    path("songs/<int:song_id>/", views.song_detail, name="song_detail"),
]