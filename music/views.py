from django.shortcuts import render
from .models import Song

def song_list(request):
    songs = Song.objects.all()
    return render(request, "music/song_list.html", {"songs": songs})

