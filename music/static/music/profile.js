// First check if User is already spotify authenticated
// For this we'll check if it has an access token AND if the refresh token hasn't expired

document.addEventListener('DOMContentLoaded', function() {
    setGradients();
    document.querySelector('.playlists').style.display = 'none';
    document.querySelector('#stored_button').addEventListener('click', () => {
        displayStored('stored');    
    });
    document.querySelector('#spotify_button').addEventListener('click', () => {
        displayStored('spotify');    
    });
    // Hide the two types of playlists
    document.querySelector('#stored_playlists').style.display = 'none';
    document.querySelector('#spotify_playlists').style.display = 'none';

    // If scrolled to the bottom, load more spotify pages
    window.onscroll = () => {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
            offset = document.querySelector('.playlists').dataset.offset;
            if (offset !== '0') {
                loadPlaylists(offset);
            }
        }
    };
});

checkSpotifyStatus();

async function checkSpotifyStatus() {
    let resultado = await isSpotifyAuthenticated();
    if (resultado) {
        console.log("Spotify authenticated");

        // Show profile
        fetchProfile();
    } else {
        console.log("No spotify authenticated");
        getAuthorizationURL();
    }
}

function getAuthorizationURL() {
    fetch(`/get-auth-url`, {
        method: "GET"
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        document.location = result.url;
    });
    return true;
}

async function isSpotifyAuthenticated() {
    let resultado;
    await fetch(`/is-spotify-authenticated`, {
        method: "GET"
    })
    .then(response => response.json())
    .then(result => {
        resultado = result.status;
    });
    return resultado;
}

async function fetchProfile() {
    await fetch(`/get-profile`, {
        method: "GET"
    })
    .then(response => response.json())
    .then(profile => {
        document.querySelector('#sessionName').innerHTML = profile.display_name;
        document.getElementById("pais").innerText = profile.country;
        document.getElementById("seguidores").innerText = profile.followers.total;
    });
    

}

async function loadPlaylists(offset) {
    // ------------- Playlists -------------------
    fetch(`/get-playlists?offset=${offset}`, {
        method: "GET"
    })
    .then(response => response.json())
    .then(data => {
        playlists = data.playlists;
        // select playlists block
        content = document.querySelector('.playlists');
        content.style.display = 'flex';

        playlists.forEach(playlist => {
            // Check if the playlist is already stored locally (displayed on the stored section)
            const is_displayed = document.querySelector(`#stored_playlist_${playlist.id}`);
            if (is_displayed === null){
                // Load each playlist
                card = document.createElement('div');
                card.classList.add('card');
                card.setAttribute('id', `playlist_${playlist.id}`)
                card.style.width = '18rem';
                let image = "";
                if (playlist.images[0]) {
                    image = playlist.images[0].url;
                }
                else {
                    image = 'https://user-images.githubusercontent.com/24848110/33519396-7e56363c-d79d-11e7-969b-09782f5ccbab.png';
                }
                card.innerHTML = `
                <div class="card-body">
                    <img class="card-img-top" src="${image}"></img>
                    <h5 class="card-title">${playlist.name}</h5>
                    <p class="card-text">${playlist.description}</p>
                    <br/>
                    <button class="btn btn-primary" onclick="storePlaylist('${playlist.id}')"><i class="bi bi-file-earmark-arrow-down"></i> Save</button>
                </div>
                `
                content.append(card);
            }
        });
        // Remove button 
        document.querySelector('#synchronize').style.display = 'none';
        document.querySelector('.playlists').dataset.offset = data.offset;
    });

}

function storePlaylist(playlist_id) {
    fetch(`store-playlist`, {
        method: "POST",
        body: JSON.stringify({
            playlist_id: playlist_id
        })
    })
    .then(response => response.json())
    .then(playlist => {
        // Prepare information to aapend to upper (stored) playlists
        content = document.querySelector('.upper-playlists');
        content.style.display = 'flex';

        // Erase this card and add it to the 'My stores playlists' to give the 
        // efect of moving it to the top
        card = document.createElement('div');
        card.classList.add('card');
        card.setAttribute('id', `stored_playlist_${playlist.id}`)
        card.style.width = '18rem';
        let image = "";
        if (playlist.images[0]) {
            image = playlist.images[0].url;
        }
        else {
            image = 'https://user-images.githubusercontent.com/24848110/33519396-7e56363c-d79d-11e7-969b-09782f5ccbab.png';
        }
        card.innerHTML = `
        <div class="card-body">
            <img class="card-img-top" src="${image}">
            <h5 class="card-title"><a href="playlist/${playlist.id}">${playlist.name}</a></h5>
            <p class="card-text">${playlist.description}</p>
            <br/>
            <hr>
            <button onclick="updateFollow('${playlist.id}')" class="btn btn-outline-warning btn-sm"
            data-status='unfollow' id="playlist_${playlist.id}">Unfollow</button>
        </div>
        `
        content.append(card);
    });
    // Delete the duplicated playlist
    const playlist_to_remove = document.querySelector(`#playlist_${playlist_id}`);
    playlist_to_remove.remove();
}

function updateFollow(playlist_id) {

    // If action == follow is because the action will be to follow
    // else the 'unfollow' tag will be to unfollow the playlist

    action = document.querySelector(`#playlist_${playlist_id}`).dataset.status;

    if (action === 'follow') {
        method = 'PUT';
    } else if (action === 'unfollow') {
        method = 'DELETE';
    }
    
    fetch('/update-follow', {
        method: method, 
        body: JSON.stringify({
            'playlist_id': playlist_id
        })
    })
    .then(response => response.json())
    .then(result => {
        // Change actions based on 'action' variable
        if (result.message === 'successful') {
            change = document.querySelector(`#playlist_${playlist_id}`);
            
            if (action === 'follow') {
                change.dataset.status = 'unfollow';
                change.classList.remove('btn-info');
                change.classList.add('btn-outline-warning');
                change.innerHTML = 'Unfollow';
            } else if (action === 'unfollow') {
                change.dataset.status = 'follow';
                change.classList.remove('btn-outline-warning');
                change.classList.add('btn-info');
                change.innerHTML = 'Follow';
            }
            
        }
    });

}

function displayStored(collapse_tag) {
    if (collapse_tag === 'stored') {
        // Hide the other element
        toHide = document.querySelector('#spotify_playlists');
        toHide.style.display = 'none';
        toHide.dataset.status = 'hidden';

        //Changes on the currentDiv
        currentDiv = document.querySelector('#stored_playlists');
        if (currentDiv.dataset.status === 'hidden') {
            currentDiv.style.display = 'block';
            currentDiv.dataset.status = 'showing';
        } else if (currentDiv.dataset.status === 'showing') {
            currentDiv.style.display = 'none';
            currentDiv.dataset.status = 'hidden'
        }
    } else if (collapse_tag === 'spotify') {
        // Hide and change the other element
        toHide = document.querySelector('#stored_playlists');
        toHide.style.display = 'none';
        toHide.dataset.status = 'hidden';

        currentDiv = document.querySelector('#spotify_playlists');
        if (currentDiv.dataset.status === 'hidden') {
            currentDiv.style.display = 'block';
            currentDiv.dataset.status = 'showing';
        } else if (currentDiv.dataset.status === 'showing') {
            currentDiv.style.display = 'none';
            currentDiv.dataset.status = 'hidden'
        }
    }

}


function setGradients() {
    cards = document.querySelectorAll('.card');

    cards.forEach(card => {
        // Get colors
        color1 = card.dataset.primary_color;
        color2 = card.dataset.secondary_color;
        color1 += 'bd';
        color2 += 'bd';

        // Set backgroudn color to default
        card.style.backgroundColor = 'white';

        // Change background linear with JavaScript
        card.style.backgroundImage = 
        "linear-gradient(to top, "+ color1 +", "+ color2 +")";

    });
}