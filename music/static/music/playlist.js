const tags = []

document.addEventListener('DOMContentLoaded', function () {
    document.querySelector('.playlist_edit').style.display = 'none';
    document.querySelector('#input_tags').style.display = 'none';
    let storeTagsButton = document.querySelector('#storeTagsButton');
    if (storeTagsButton) {
        storeTagsButton.style.display = 'none';
    }

        // Set color of the playlists according to primary and secondary colors
    div_color = document.querySelector('#playlist_image_div');
    color1 = div_color.dataset.color;
    color2 = div_color.dataset.color2;
    div_color.style.backgroundImage = 
    "linear-gradient(to top, "+ color1 +", "+ color2 +")";

    // Set color from both hex color inputs
    document.querySelector('#hex_color_input').addEventListener("input", (event) => {
        div_color = document.querySelector('#playlist_image_div');
        color1 = event.target.value;
        color2 = document.querySelector('#hex_color_input_second').value;
        div_color.style.backgroundImage = 
        "linear-gradient(to top, "+ color1 +", "+ color2 +")";
    });

    document.querySelector('#hex_color_input_second').addEventListener("input", (event) => {
        div_color = document.querySelector('#playlist_image_div');
        color1 = document.querySelector('#hex_color_input').value;
        color2 = event.target.value;
        console.log(color1, color2);
        div_color.style.backgroundImage = 

        "linear-gradient(to top, "+ color1 +", "+ color2 +")";
    });

    // Update reach (public or private)
    reach = document.querySelector('#playlist_reach').dataset.playlist_reach;
    if (reach === 'True') {
        document.querySelector('#playlist_reach').dataset.playlist_reach = 'public';
        changeButtons('public');
    } else if (reach == 'False') {
        document.querySelector('#playlist_reach').dataset.playlist_reach = 'private';
        changeButtons('private');
    }

    // Load current tags
    const tags_div = document.querySelector('.playlist_tags_span').getElementsByTagName('span');
    
    // Had to conver to Array object in order to iterate using forEach
    Array.from(tags_div).forEach((tag)=> {
        tags.push(tag.dataset.category);
    })
    
    // Load each song for the 
    playlist_id = document.querySelector('#playlist_id').innerHTML;
    loadSongs(playlist_id);


});


function editPlaylist() {
    // Change the module
    const content = document.querySelector('.playlist_details_info');
    content.style.display = 'none';

    // Show Edit part
    document.querySelector('.playlist_edit').style.display = 'flex';
    description = content.querySelector('#description').innerHTML;
    document.querySelector('#playlist_description').innerHTML = description;
    
}

function changeButtons(button_pressed) {
    public = document.querySelector('#playlist_public');
    private = document.querySelector('#playlist_private');

    if (button_pressed === 'private') {
        public.classList.remove('btn-warning');
        public.classList.add('btn-outline-warning');
        private.classList.remove('btn-outline-info');
        private.classList.add('btn-info');
        document.querySelector('#playlist_reach').dataset.playlist_reach = 'private';

    } else if(button_pressed === 'public') {
        private.classList.remove('btn-info');
        private.classList.add('btn-outline-info');
        public.classList.remove('btn-outline-warning');
        public.classList.add('btn-warning');
        document.querySelector('#playlist_reach').dataset.playlist_reach = 'public';
    }
}

function updatePlaylist(playlist_id) {
    description = document.querySelector('#playlist_description').value;
    reach = document.querySelector('#playlist_reach').dataset.playlist_reach;
    playlist_color = document.querySelector('#hex_color_input').value;
    playlist_secondary_color = document.querySelector('#hex_color_input_second').value;

    // Use fetch call to update playlist (spotify and locally)
    fetch('/update-playlist', {
        method: 'PUT', 
        body: JSON.stringify({
            description: description,
            reach: reach,
            playlist_id: playlist_id,
            playlist_color: playlist_color,
            playlist_secondary_color: playlist_secondary_color
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.message === 'playlist updated') {
            // Change content block
            content = document.querySelector('.playlist_details_info');
            content.style.display = 'block';
            
            // Change description
            description = content.querySelector('#description');
            description.innerHTML = result.description;

            
            document.querySelector('.playlist_edit').style.display = 'none';

        }
    });
    return false;
}

function cancelEdit() {
    document.querySelector('.playlist_edit').style.display = 'none';
    document.querySelector('.playlist_details_info').style.display = 'block';
}

function addTags() {
    // Select the content div of the tags (each one a span)
    tags_div = document.querySelector('.playlist_tags_span');

    // Input text for the tags
    input_tags = document.querySelector('#input_tags');
    input_tags.style.display = 'block';
    input_tags.addEventListener('keyup', function(event) {
        if (event.key === 'Enter' && input_tags.value != '') {
            // Create span element and append elements
            new_span = document.createElement('span');
            new_span.dataset.category = input_tags.value;
            new_span.innerHTML = `${input_tags.value} <a href='javascript:deleteTag("${input_tags.value}")'> x </a>`;

            // Update tags array
            tags.push(input_tags.value);
            
            // Append new <span> element and update input field
            tags_div.append(new_span);
            input_tags.value = '';
            updateTags();
        }
    });

    document.querySelector('#addTagsButton').style.display = 'none';
    document.querySelector('#storeTagsButton').style.display = 'block';
}

function updateButtons() {
    document.querySelector('#addTagsButton').style.display = 'block';
    document.querySelector('#storeTagsButton').style.display = 'none';
    document.querySelector('#input_tags').style.display = 'none';
}

function updateTags() {
    playlist_id = document.querySelector('#playlist_id').innerHTML;
    fetch('/update-tags', {
        method: 'PUT',
        body: JSON.stringify({
            tags: tags,
            playlist_id: playlist_id
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
    })
} 

function deleteTag(category) {
    let confirmation;
    if (confirm("Do you want to delete the tag?") == true) {
        confirmation = "Pressed true";
    } else {
        return false;
    } 

    playlist_id = document.querySelector('#playlist_id').innerHTML;

    // Delete from the array
    index = tags.indexOf(category);
    tags.splice(index, 1);

    // Delete span tag
    to_delete = document.querySelector(`[data-category=${category}]`);
    to_delete.remove();

    // Fetch call to delete from database
    fetch('/delete-tag', {
        method: 'PUT',
        body: JSON.stringify({
            playlist_id: playlist_id,
            tag: category
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
    });

}


function loadSongs(playlist_id) {
    fetch(`/load-songs?playlist_id=${playlist_id}`, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(result => {

        // Get the songs which are called 'items'
        songs = result.items;
        console.log(result);

        // Create a division for each playlist
        songs_div = document.querySelector('#songs_view');
        songs_div.style.display = 'block';

        songs.forEach(song => {
            // Get artists
            const artists = new Array();
            creators = song.track.artists;
            creators.forEach(creator => {
                artists.push(creator.name);
            });

            song_div = document.createElement('div');
            song_div.classList.add('song');
            song_div.innerHTML = `
                <div class="song-play">
                    <a href="javascript:playSong('${song.track.uri}', '${song.track.album.uri}')"><i class="bi bi-play-circle"></i></a>
                </div>
                <div class="song-info">
                    <a target="_blank" href=${song.track.external_urls.spotify}><span>${song.track.name}</span></a>
                    <a><span>${artists}</span></a>
                </div>
            `;
            songs_div.append(song_div);
        });
        
    });
}

function playSong(song_uri, album_uri) {
    
    fetch('/play-song', {
        method: 'PUT',
        body: JSON.stringify({
            'song_uri': song_uri,
            'album_uri': album_uri
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
    });

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
            change.remove(); 
            
        }
    });

}