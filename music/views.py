from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json # Library to serialize
from django.core.paginator import Paginator

# Spotify API
from .credentials import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET
from django.shortcuts import render
from rest_framework.views import APIView

from requests import Request, post, get, put, delete # Library to send HTTP requests
from rest_framework import status # Used for the status.HTTP_200_OK
from rest_framework.response import Response # Maybe change

from .util import update_or_create_user_tokens, is_spotify_authenticated, get_user_tokens # util

from .models import SpotifyToken, User, Playlist, Tag, Song, UserFollowingPlaylist

from urllib.parse import urlparse, parse_qs # From Python, used to get the offset from the spotify API

def authURL(request):
    # My own scopes: 
    scopes = 'user-read-private user-read-email playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative user-modify-playback-state'

    # The next will prepare the URL so the frontend will actually send it
    url = Request('GET', 'https://accounts.spotify.com/authorize', params= {
        'scope':scopes,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID
    }).prepare().url

    return JsonResponse({"url": url}, status=200)
    # return Response({'url': url}, status=status.HTTP_200_OK)

@csrf_exempt
def spotify_callback(request):
    code = request.GET.get('code')

    # From the Library POST, this part will actually make a request to spotify, not on the frontend
    response = post('https://accounts.spotify.com/api/token', data={
        'grant_type' : 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET 
    }).json() # Gets the Json from the post request

    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    error = response.get('error')

    if request.user.is_authenticated:
        update_or_create_user_tokens(request.user, access_token, token_type, 
                                    expires_in, refresh_token)
        
        # Add spotify id to user
        access_token = get_user_tokens(request.user).access_token
        headers = {'Authorization': f'Bearer {access_token}'}
        profile_response = get('https://api.spotify.com/v1/me', headers=headers).json()

        spotify_id = profile_response['id']
        user_to_update = User.objects.filter(username=request.user).first()
        user_to_update.spotify_id = spotify_id
        user_to_update.save()
        user_playlist_relation = UserFollowingPlaylist(userFollowing=request.user)
        user_playlist_relation.save()
        return HttpResponseRedirect(reverse("profile")) 

def spotify_authentication(request):
    is_authenticated = is_spotify_authenticated(request.user)
    return JsonResponse({'status':is_authenticated}, status=200)

def show_profile(request):
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}'}

    response = get('https://api.spotify.com/v1/me', headers=headers).json()

    return JsonResponse(response)

def show_playlists(request):
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}'}
    offset = request.GET.get('offset', 0)
    if offset == 'undefined':
        offset = 0
    # 'offset' if nothing then it'll return from the first album (offset is the index where to start the playlists to return)
    response = get(f'https://api.spotify.com/v1/me/playlists?limit=50&offset={offset}', headers=headers).json()
    playlists_items = response['items']
    playlists = [playlist for playlist in playlists_items]

    next_offset = 0
    if response['next']:
        parsed_url = urlparse(response['next'])
        next_offset = parse_qs(parsed_url.query)['offset'][0]


    data = {'offset': next_offset,
            'playlists': playlists 
    }
    return JsonResponse(data=data, safe=False)

def show_playlist(request, playlist_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
    current_user = User.objects.filter(username=request.user).first()

    # Load tags
    tags = Tag.objects.filter(playlists__playlist_id=playlist_id)

    color = playlist.background_color
    color2 = playlist.secondary_color

    return render(request, "music/playlist.html", {
        'playlist': playlist,
        'current_user': current_user,
        'tags': tags,
        'color': color,
        'color2': color2
    })

def create(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login")) 

    if request.method == 'GET':
        return render(request, "music/create.html")
@csrf_exempt
def store_playlist(request):
    data = json.loads(request.body)
    playlist_id = data.get('playlist_id')
    
    # Check wether the playlist is already store
    is_stored = Playlist.objects.filter(playlist_id=playlist_id).first()
    if(is_stored):
        return JsonResponse({'message': 'Playlist already stored'}, status=200)
    
    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}'}

    # First get playlist
    response = get(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers).json()

    # Extract the data and make a new Playlist object
    creator = response['owner']['display_name'] 
    creator_id = response['owner']['id']
    image = response['images'][0]['url'] if response['images'] else 'No image'
    name = response['name']
    description = response['description'] if response['description'] else 'No description'
    is_public = response['public']
    playlist = Playlist(playlist_id=playlist_id, creator=creator, image=image, name=name,
                        description=description, is_public=is_public, creator_id=creator_id)
    playlist.save()

    # Store on the user's database (playlist to follow)
    # Check if the UserFollowing instance already exists
    relation_exists = UserFollowingPlaylist.objects.filter(userFollowing=request.user)
    if not relation_exists: # If it doesn't exist
        print("Doesn't exist")
        user_playlist_relation = UserFollowingPlaylist(userFollowing=request.user)
        user_playlist_relation.save()
        user_playlist_relation.playlists.add(playlist)
        user_playlist_relation.save()
    else:
        print("Exists")
        user_playlist_relation = relation_exists.first()
        user_playlist_relation.playlists.add(playlist)
        user_playlist_relation.save()

    return JsonResponse(response, status=200)

@csrf_exempt
def create_playlist(request):

    data = json.loads(request.body)
    name = data.get('playlist_name', "")
    description = data.get('description')
    reach = data.get('reach')
    collaborative = data.get('collaborative')

    if reach == 'private':
        reach = False
    elif reach == 'public':
        reach = True

    # is_spotify_authenticated assumes the user's logged in and we call it only to
    # update if the expiry date have been dated out
    is_spotify_authenticated(request.user)

    # First get the user's id
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}'}

    response = get('https://api.spotify.com/v1/me', headers=headers).json()
    userID = response['id']
    
    # Create playlist with API call
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    data = {'name': name, 'description': description, 'public': reach, 'collaborative': collaborative}

    response = post(f'https://api.spotify.com/v1/users/{userID}/playlists', headers=headers, data=json.dumps(data)).json()

    # Get playlist id that is in spotify

    # Create playlist on the database
    playlist_id = response['id']
    new_playlist = Playlist(creator=request.user.username, name=name, is_public=reach, description=description,
                    creator_id=userID, playlist_id=playlist_id)
    new_playlist.save()

    return JsonResponse({'message': 'playlist created'}, status=200)

@csrf_exempt
def update_playlist(request):
    body = json.loads(request.body)

    description = body.get('description', '')
    is_public = body.get('reach', '')
    if is_public == 'public':
        is_public = True
    elif is_public == 'private':
        is_public = False
    
    playlist_id = body.get('playlist_id', '')

    # Update on spotify's database
    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    # Check data
    data = {
        "name": "Updated Playlist Name",
        "description": "Updated playlist description",
        "public": False 
    }
    testing = json.dumps(data)

    response = put(f'https://api.spotify.com/v1/playlists/{playlist_id}', headers=headers, data=data)

    # Update playlist from the database
    playlist_id = body.get('playlist_id')
    playlist_color = body.get('playlist_color')
    playlist_secondary_color = body.get('playlist_secondary_color')
    playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
    playlist.background_color = playlist_color
    playlist.secondary_color = playlist_secondary_color
    playlist.description = body.get('description')
    playlist.save()    
    
    return JsonResponse({'message': 'playlist updated', 
    'description': description}, status=200)

def explore(request):
    if request.method == "GET":
        # Get playlists
        playlists = Playlist.objects.filter(is_public=True)

        tags = Tag.objects.all()

        return render(request, "music/explore.html", {
            'playlists': playlists,
            'tags': tags
        })



def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "music/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "music/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "music/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "music/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "music/register.html")


def index(request):
    if request.method == 'GET':
        # Load all playlists
        playlists = Playlist.objects.all()

        return render(request, "music/index.html", {
            'playlists': playlists
        })

def profile(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login")) 

    if request.method == 'GET':
        # Get playlist from the user (user_playlists is a lists of ids)
        user_playlists = Playlist.objects.filter(playlists_following__userFollowing=request.user)

        # Filter playlists that the user follows in order to change the follow and unfollow buttons
        # Get playlists user follows

        return render(request, "music/profile.html", {
            "playlists": user_playlists 
        })

@csrf_exempt
def update_tags(request):
    data = json.loads(request.body)
    tags = data.get('tags', '')
    playlist_id = data.get('playlist_id')
    playlist = Playlist.objects.filter(playlist_id=playlist_id).first()

    # Create new tag if it doesn't exist
    for category in tags:
        tag_exists = Tag.objects.filter(category=category)
        if not tag_exists.exists():
            new_tag = Tag(category=category)
            new_tag.save()
            new_tag.playlists.add(playlist)
        else:
            # If it exists but the playlist doesn't have it, then
            # add it to palylist
            tag_exists.first().playlists.add(playlist)

    return JsonResponse({'message': 'Tags updated'}, status=200)

@csrf_exempt
def delete_tag(request):
    data = json.loads(request.body)

    playlist_id = data.get('playlist_id', '')
    category = data.get('tag', '')

    playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
    tag = Tag.objects.filter(category=category).first()
    tag.playlists.remove(playlist)

    return JsonResponse({'message': 'tag erased'}, status=200)


def show_filtered_playlists(request):
    # Convert from string to array
    tags = request.GET.get('tags')
    tags = tags.split(",")

    # Important, logic of the following relationship:
    # From the related_name field in tags, access from parent to child where the category is in the 'tags' array
    playlists = Playlist.objects.filter(related_playlists__category__in=tags)
    playlists = [playlist.serialize() for playlist in playlists]

    for playlist in playlists:
        tags = []
        tags_querySet = Tag.objects.filter(playlists__playlist_id=playlist['playlist_id'])
        for tag in tags_querySet:
            tags.append(tag.category)

        playlist['tags'] = tags

    data = {
        'message': 'Playlists loaded successfully',
        'playlists': playlists
    }

    return JsonResponse(data, status=200)


def show_recommended(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login")) 

    # Show recommended playlists based on the tags that the user follows

    # First get the playlists the user follows
    playlists = Playlist.objects.filter(playlists_following__userFollowing=request.user)

    # Get the tags for playlists the user follows
    # Didn't have to iterate through each playlist, only get tags where playlists are in those the user follows
    results = Tag.objects.filter(playlists__in=playlists).values_list('category') # For some reason had to use values_list

    # With the results, find those playlists that the user don't follow
    # Logic: Get playlists where tag is in result but the user doesn't follow
    playlists_to_exclude = playlists.values_list('id') # Get given ids of the playlists to exclude

    # First filter: Get all playlists with the tags that the user follows
    recommendations = Playlist.objects.filter(related_playlists__category__in=results)

    # Second filter: Exclude the playlists that the user already follows
    output = recommendations.exclude(playlists_following__userFollowing=request.user)

    return render (request, "music/recommended.html", {
        'playlists': output
    }) 

# Show a specific category
def show_explore_category(request, category):
    # Load playlists
    playlists = Playlist.objects.filter(related_playlists__category=category)

    return render(request, "music/index.html", {
        'playlists': playlists
    })

@csrf_exempt
def unfollow_playlist(request):
    data = json.loads(request.body)
    playlist_id = data.get('playlist_id', '')

    # Update and get access token
    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token

    # Unfollow with the spotify API     
    headers = {'Authorization': f'Bearer {access_token}'}

    response = delete(f'https://api.spotify.com/v1/playlists/{playlist_id}/followers', headers=headers)

    message = "Default message"
    if response.status_code == 200:
        message = 'successful'
    else:
        message = 'unsuccessful'


    return JsonResponse({'message': message})

@csrf_exempt
def follow_playlist(request):

    data = json.loads(request.body)
    playlist_id = data.get('playlist_id', '')

    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token

    # Follow with the spotify API     
    headers = {'Authorization': f'Bearer {access_token}'}

    response = put(f'https://api.spotify.com/v1/playlists/{playlist_id}/followers', headers=headers)
    print(response)

    message = "Default message"
    if response.status_code == 200:
        message = 'successful'
    else:
        message = 'unsuccessful'


    return JsonResponse({'message': message})

@csrf_exempt
def update_follow(request):
    data = json.loads(request.body)
    playlist_id = data.get('playlist_id', '')

    # Update and get access token
    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token

    # Unfollow with the spotify API     
    headers = {'Authorization': f'Bearer {access_token}'}

    if request.method == 'DELETE':
        response = delete(f'https://api.spotify.com/v1/playlists/{playlist_id}/followers', headers=headers)

    elif request.method == 'PUT':
        response = put(f'https://api.spotify.com/v1/playlists/{playlist_id}/followers', headers=headers)

    message = "Default message"
    if response.status_code == 200:
        message = 'successful'
    else:
        message = 'unsuccessful'

    # Update on the database
    if request.method == 'DELETE':
        toErasePlaylist = Playlist.objects.filter(playlist_id=playlist_id).first()
        toEraseRelation= UserFollowingPlaylist.objects.filter(userFollowing=request.user).first()
        toEraseRelation.playlists.remove(toErasePlaylist)
        toEraseRelation.save()
    else:
        toFollowPlaylist= Playlist.objects.filter(playlist_id=playlist_id).first()
        toUpdatePlaylist = UserFollowingPlaylist.objects.filter(userFollowing=request.user).first()
        toUpdatePlaylist.playlists.add(toFollowPlaylist)

    return JsonResponse({'message': message})

def load_songs(request):

    playlist_id = request.GET.get('playlist_id')

    # Spotify API data
    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}'}

    fields = f''

    songs = get(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?{fields}', headers=headers)

    if songs.status_code == 200:
        response = songs.json()
    else:
        response = {'message': 'Unsuccessful'} 

    return JsonResponse(response, status=200)

@csrf_exempt
def play_song(request):
    
    data = json.loads(request.body)
    song_uri = data.get('song_uri')
    
    # Spotify API data
    is_spotify_authenticated(request.user)
    access_token = get_user_tokens(request.user).access_token
    headers = {'Authorization': f'Bearer {access_token}'}

    data = {
        'uris': [song_uri]
    }

    response = put('https://api.spotify.com/v1/me/player/play', headers=headers, data=json.dumps(data))

    print(response)

    return JsonResponse({'message': 'playing'}, status=200)