
from datetime import timedelta
import logging

from mutagen import File as MutagenFile

from django.conf import settings
from django.db import models
from django.utils import timezone


logger = logging.getLogger(__name__)


def format_duration(seconds):
    seconds = int(round(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"

    return f"{minutes}:{seconds:02d}"


class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    duration_seconds = models.PositiveIntegerField()
    is_explicit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.FileField(
        upload_to='songs/',
        blank=True,
        null=True
    )
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
        return format_duration(self.duration_seconds)

    def refresh_audio_duration(self):
        """Read the actual duration from the uploaded audio file."""
        if not self.audio_file:
            return False

        try:
            with self.audio_file.open("rb") as audio_file:
                audio = MutagenFile(audio_file)

                if audio and audio.info and audio.info.length:
                    actual_duration = int(round(audio.info.length))

                    Song.objects.filter(pk=self.pk).update(
                        duration_seconds=actual_duration
                    )

                    self.duration_seconds = actual_duration
                    return True

        except Exception:
            logger.exception(
                "Could not read audio duration for song %s",
                self.pk
            )

        return False

    def save(self, *args, **kwargs):
        audio_changed = self._state.adding

        if not self._state.adding and self.pk:
            old_audio = (
                Song.objects.filter(pk=self.pk)
                .values_list("audio_file", flat=True)
                .first()
            )

            audio_changed = old_audio != (
                self.audio_file.name if self.audio_file else ""
            )

        super().save(*args, **kwargs)

        if audio_changed and self.audio_file:
            self.refresh_audio_duration()


class EmailOTP(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now=True)
    attempts = models.PositiveSmallIntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.user}"


class Playlist(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="playlists",
    )
    name = models.CharField(max_length=100)
    songs = models.ManyToManyField(
        Song,
        blank=True,
        related_name="playlists"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.owner})"


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="likes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "song"],
                name="unique_user_song_like"
            )
        ]

    def __str__(self):
        return f"{self.user} likes {self.song}"
