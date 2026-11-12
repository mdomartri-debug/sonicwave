from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    duration_seconds = models.PositiveIntegerField()
    is_explicit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.FileField(upload_to='songs/', blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="songs",
    )

    def __str__(self):
        return f"{self.title} by {self.artist}"

    def length(self):
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"


class EmailOTP(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.user}"