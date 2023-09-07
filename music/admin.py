from django.contrib import admin

# Import models
from .models import User, Playlist, Tag, SpotifyToken, UserFollowingPlaylist

# Register your models here.
admin.site.register(User)
admin.site.register(Playlist)
admin.site.register(Tag)
admin.site.register(SpotifyToken)
admin.site.register(UserFollowingPlaylist)