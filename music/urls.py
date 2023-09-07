from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create, name="create"), 
    path("profile", views.profile, name="profile"),

    # My routes for SPOTIFY API
    path("get-auth-url", views.authURL, name="authorization"),
    path("redirect", views.spotify_callback, name="redirect"),
    path("is-spotify-authenticated", views.spotify_authentication, name="spotify_authenticated"),
    path("get-profile", views.show_profile, name="get_profile"),

    path("get-playlists", views.show_playlists, name="current_playlists"),
    path("create-playlist", views.create_playlist, name="create_playlist"),
    path("store-playlist", views.store_playlist, name="store_playlist"),
    path("explore", views.explore, name="explore"),
    path("playlist/<str:playlist_id>", views.show_playlist, name="show_playlist"),
    path("update-playlist", views.update_playlist, name="update_playlist"),
    path("update-tags", views.update_tags, name="update_tags"),
    path("delete-tag", views.delete_tag, name="delete_tag"),
    path("show-playlists-filtered", views.show_filtered_playlists, name="show_filtered"),
    path("recommended", views.show_recommended, name="recommended"),
    path("explore/<str:category>", views.show_explore_category, name="show_explore_category"),
    path("unfollow-playlist", views.unfollow_playlist, name="unfollow_playlist"),
    path("follow-playlist", views.follow_playlist, name="follow_playlist"),
    path("update-follow", views.update_follow, name="update_follow"),
    path("load-songs", views.load_songs, name="load_songs"),
    path("play-song", views.play_song, name="play_song")

]
