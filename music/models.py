from django.db import models

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200)
    duration_seconds = models.PositiveIntegerField()
    is_explicit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    audio_file = models.FileField(upload_to='songs/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} by {self.artist}"

    def length(self):
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"
    
