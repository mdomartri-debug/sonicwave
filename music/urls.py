from django.urls import path
from . import views

urlpatterns = [
    path("songs/", views.song_list, name="song_list"),
]