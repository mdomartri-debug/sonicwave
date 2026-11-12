import secrets

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404, redirect

from .forms import RegisterForm
from .models import Song, EmailOTP

User = get_user_model()

MAX_ATTEMPTS = 5


def song_list(request):
    songs = Song.objects.all()
    return render(request, "music/song_list.html", {"songs": songs})


def song_detail(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    return render(request, "music/song_detail.html", {"song": song})


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
    })