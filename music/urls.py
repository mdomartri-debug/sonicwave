from django.urls import path
from . import views

urlpatterns = [
    path("songs/", views.song_list, name="song_list"),
    path("songs/<int:song_id>/", views.song_detail, name="song_detail"),
    path("upload/", views.upload_song, name="upload_song"),
    path("register/", views.register, name="register"),
    path("verify/", views.verify_otp, name="verify_otp"),
    path("resend/", views.resend_otp, name="resend_otp"),
]