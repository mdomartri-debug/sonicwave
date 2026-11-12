from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Song

User = get_user_model()

MAX_UPLOAD_MB = 50


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class SongUploadForm(forms.ModelForm):
    copyright_confirmed = forms.BooleanField(
        required=True,
        label="I own this music or have permission to upload it",
    )

    class Meta:
        model = Song
        fields = ["title", "artist", "audio_file", "is_explicit"]

    def clean_audio_file(self):
        audio = self.cleaned_data.get("audio_file")

        if not audio:
            raise forms.ValidationError("Please choose an audio file.")

        if audio.size > MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(
                f"File is too large. Maximum size is {MAX_UPLOAD_MB} MB."
            )

        return audio