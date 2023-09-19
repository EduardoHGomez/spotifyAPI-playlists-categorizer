from django.contrib.auth.models import AbstractUser
from django.db import models

# User

class SpotifyToken(models.Model):
    user = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    refresh_token = models.CharField(max_length=300)
    access_token = models.CharField(max_length=300)
    expires_in = models.DateTimeField()
    token_type = models.CharField(max_length=50)

    def serialize(self):
        return {
            "user": self.user,
            "created_at": self.created_at,
            "refresh_token": self.refresh_token,
            "access_token": self.access_token,
            "expires_in": self.expires_in,
            "token_type": self.token_type
        }


class User(AbstractUser):
    spotify_id = models.CharField(max_length=50, default="No_id")

class Playlist(models.Model):
    creator = models.CharField(max_length=80, default="No name")
    name = models.CharField(max_length=80, default='No field filled')
    pinned = models.BooleanField(default=False)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    playlist_id = models.CharField(max_length=100, default='No field filled')
    image = models.URLField(max_length=255, default='https://cdn1.iconfinder.com/data/icons/business-company-1/500/image-512.png')
    background_color = models.CharField(max_length=9, default='#ffffff')
    secondary_color = models.CharField(max_length=9, default="#ffffff")
    description = models.CharField(max_length=400, default='No field filled')
    is_public = models.BooleanField(default=False)
    creator_id = models.CharField(max_length=80, default="No spotify id")

    def __str__(self):
        return f"Playlist by {self.creator}, name: {self.name}"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "creator": self.creator,
            "playlist_id": self.playlist_id,
            "image": self.image,
            "background_color": self.background_color,
            "description": self.description,
            "is_public": self.is_public,
            "creator_id": self.creator_id,
            "secondary_color": self.secondary_color
        }

class UserFollowingPlaylist(models.Model):
    userFollowing = models.ForeignKey(User, on_delete=models.CASCADE, related_name="UserFollowsThisPlaylist")
    playlists = models.ManyToManyField(Playlist, related_name="playlists_following")

    def __str__(self):
        return f"Playlists that {self.userFollowing} follows"

class Tag(models.Model):
    playlists = models.ManyToManyField(Playlist, related_name="related_playlists")
    category = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.category}"

    def serialize(self):
        return {
            'category': self.category
        }


# Class that represent a song, where the playlist will have
class Song(models.Model):
    title = models.CharField(max_length=255)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="playlist_with_song")
    # 'playlist' has to be one to many