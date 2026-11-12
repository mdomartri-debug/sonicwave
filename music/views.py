import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from mutagen import File as MutagenFile

from .forms import RegisterForm, SongUploadForm
from .models import Song, EmailOTP, Like, Playlist

User = get_user_model()

MAX_ATTEMPTS = 5
MAX_DURATION_SECONDS = 60 * 60  # 1 hour


def song_list(request):
    songs = Song.objects.all()
    liked_ids = []
    playlists = []
    if request.user.is_authenticated:
        liked_ids = list(
            Like.objects.filter(user=request.user).values_list("song_id", flat=True)
        )
        playlists = Playlist.objects.filter(owner=request.user)
    return render(request, "music/song_list.html", {
        "songs": songs,
        "liked_ids": liked_ids,
        "playlists": playlists,
    })


def song_detail(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    return render(request, "music/song_detail.html", {"song": song})


@login_required
def upload_song(request):
    if request.method == "POST":
        form = SongUploadForm(request.POST, request.FILES)
        if form.is_valid():
            audio_file = form.cleaned_data["audio_file"]

            # Read the real audio info with mutagen
            try:
                audio_file.seek(0)
                info = MutagenFile(audio_file)
                audio_file.seek(0)
            except Exception:
                info = None

            if info is None or not hasattr(info, "info") or info.info.length <= 0:
                form.add_error("audio_file", "This is not a valid audio file.")
            else:
                duration = int(round(info.info.length))

                if duration > MAX_DURATION_SECONDS:
                    form.add_error(
                        "audio_file",
                        "This track is too long. The maximum is 60 minutes.",
                    )
                else:
                    song = form.save(commit=False)
                    song.duration_seconds = duration
                    song.uploaded_by = request.user
                    song.save()
                    return redirect("song_list")
    else:
        form = SongUploadForm()

    return render(request, "music/upload_song.html", {"form": form})


def send_otp(user):
    code = f"{secrets.randbelow(1000000):06d}"
    EmailOTP.objects.update_or_create(
        user=user,
        defaults={"code": code, "attempts": 0},
    )
    send_mail(
        subject="Your SonicWave verification code",
        message=f"Your verification code is {code}. It expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            send_otp(user)
            request.session["pending_user_id"] = user.id
            return redirect("verify_otp")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


def verify_otp(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return redirect("register")

    user = get_object_or_404(User, id=user_id)
    otp = EmailOTP.objects.filter(user=user).first()
    error = None
    notice = request.session.pop("otp_notice", None)

    if request.method == "POST":
        code = request.POST.get("code", "").strip()

        if otp is None or otp.is_expired():
            error = "This code has expired."
        elif otp.attempts >= MAX_ATTEMPTS:
            error = "Too many wrong attempts."
        elif code != otp.code:
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            error = "Wrong code. Please try again."
        else:
            user.is_active = True
            user.save()
            otp.delete()
            request.session.pop("pending_user_id", None)
            login(request, user)
            return redirect("song_list")

    return render(request, "registration/verify_otp.html", {
        "email": user.email,
        "error": error,
        "notice": notice,
    })


def resend_otp(request):
    user_id = request.session.get("pending_user_id")
    if not user_id:
        return redirect("register")

    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        otp = EmailOTP.objects.filter(user=user).first()

        if otp and timezone.now() < otp.created_at + timedelta(seconds=60):
            request.session["otp_notice"] = "Please wait a minute before requesting a new code."
        else:
            send_otp(user)
            request.session["otp_notice"] = "A new code has been sent."

    return redirect("verify_otp")


@login_required
@require_POST
def toggle_like(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    like, created = Like.objects.get_or_create(user=request.user, song=song)
    if not created:
        like.delete()

    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)
    return redirect("song_list")

@login_required
def playlist_list(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            playlist, created = Playlist.objects.get_or_create(
                owner=request.user, name=name[:100]
            )
            if created:
                messages.success(request, f'Playlist "{playlist.name}" was created.')
            else:
                messages.info(request, f'You already have a playlist named "{playlist.name}".')
        else:
            messages.error(request, "Please enter a playlist name.")
        return redirect("playlist_list")

    playlists = Playlist.objects.filter(owner=request.user)
    return render(request, "music/playlist_list.html", {"playlists": playlists})


@login_required
def playlist_detail(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
    return render(request, "music/playlist_detail.html", {
        "playlist": playlist,
        "songs": playlist.songs.all(),
    })


@login_required
@require_POST
def add_to_playlist(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    playlist_id = request.POST.get("playlist_id", "")
    if playlist_id.isdigit():
        playlist = get_object_or_404(Playlist, id=int(playlist_id), owner=request.user)
        if playlist.songs.filter(id=song.id).exists():
            messages.info(request, f'"{song.title}" is already in "{playlist.name}".')
        else:
            playlist.songs.add(song)
            messages.success(request, f'"{song.title}" was added to "{playlist.name}".')
    else:
        messages.error(request, "Please choose a playlist first.")
    return redirect("song_list")


@login_required
@require_POST
def remove_from_playlist(request, playlist_id, song_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
    song = get_object_or_404(Song, id=song_id)
    playlist.songs.remove(song)
    messages.success(request, f'"{song.title}" was removed from "{playlist.name}".')
    return redirect("playlist_detail", playlist_id=playlist.id)


@login_required
@require_POST
def delete_playlist(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
    name = playlist.name
    playlist.delete()
    messages.success(request, f'Playlist "{name}" was deleted.')
    return redirect("playlist_list")

@login_required
def liked_songs(request):
    likes = (
        Like.objects.filter(user=request.user)
        .select_related("song")
        .order_by("-created_at")
    )
    songs = [like.song for like in likes]
    return render(request, "music/liked_songs.html", {"songs": songs})