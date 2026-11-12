from django.urls import path
from . import views

urlpatterns = [
    path("songs/", views.song_list, name="song_list"),
    path("songs/<int:song_id>/", views.song_detail, name="song_detail"),
    path("songs/<int:song_id>/like/", views.toggle_like, name="toggle_like"),
    path("liked/", views.liked_songs, name="liked_songs"),
    path("songs/<int:song_id>/add-to-playlist/", views.add_to_playlist, name="add_to_playlist"),
    path("playlists/", views.playlist_list, name="playlist_list"),
    path("playlists/<int:playlist_id>/", views.playlist_detail, name="playlist_detail"),
    path("playlists/<int:playlist_id>/remove/<int:song_id>/", views.remove_from_playlist, name="remove_from_playlist"),
    path("playlists/<int:playlist_id>/delete/", views.delete_playlist, name="delete_playlist"),
    path("upload/", views.upload_song, name="upload_song"),
    path("register/", views.register, name="register"),
    path("verify/", views.verify_otp, name="verify_otp"),
    path("resend/", views.resend_otp, name="resend_otp"),
]