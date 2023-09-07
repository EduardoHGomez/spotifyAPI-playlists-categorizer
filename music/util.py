from .models import SpotifyToken
from django.utils import timezone
from datetime import timedelta
from .credentials import CLIENT_ID, CLIENT_SECRET
from requests import post

def get_user_tokens(username):
    user_tokens = SpotifyToken.objects.filter(user=username)
    if user_tokens.exists():
        return user_tokens[0] # This guarantees to return an object instead of QuerySet
    else:
        return None

def update_or_create_user_tokens(username, access_token, token_type, expires_in, refresh_token):
    tokens = get_user_tokens(username)
    expires_in = timezone.now()+ timedelta(seconds=expires_in)
    if tokens: # Update information
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=["access_token", "refresh_token", "expires_in", "token_type"])
    else: # Else create information
        tokens = SpotifyToken(user=username, access_token=access_token, refresh_token=refresh_token, 
                                token_type=token_type, expires_in=expires_in) 
        tokens.save()

# Function used in the frontend to check wether the user is spotify authenticated
# it's used inside the profile.js/checkSpotifyStatus
def is_spotify_authenticated(username):
    tokens = get_user_tokens(username)
    if tokens:
        expiry = tokens.expires_in 
        if expiry <= timezone.now():
            refresh_spotify_token(username)
        return True

    return False


def refresh_spotify_token(username):
    refresh_token = get_user_tokens(username).refresh_token
    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type':'refresh_token',
        'refresh_token':refresh_token,
        'client_id':CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }).json()

    access_token = response.get('access_token')
    token_type = response.get('token_type')
    expires_in = response.get('expires_in')

    update_or_create_user_tokens(username, access_token, token_type, expires_in, refresh_token)