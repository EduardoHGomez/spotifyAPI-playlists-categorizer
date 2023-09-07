document.addEventListener('DOMContentLoaded', function() {
    document.querySelector('#create-form').onsubmit = event => {
        event.preventDefault();
        createPlaylist();
    };
});

function createPlaylist() {
    playlist_name = document.querySelector('#playlist_name').value;
    description = document.querySelector('#playlist_description').value;
    reach = document.querySelector('#playlist_reach').dataset.playlist_reach;
    collaborative = document.querySelector('#playlist_collaborative').checked;

    fetch('/create-playlist', {
        method: 'POST',
        body: JSON.stringify({
            playlist_name: playlist_name,
            description: description,
            reach: reach,
            collaborative: collaborative,
        })
    })
    .then(response => response.json())
    .then(result => {
        console.log(result);
        document.location = '/';
    });
    return false;
}

function changeButtons(button_pressed) {
    public = document.querySelector('#playlist_public');
    private = document.querySelector('#playlist_private');

    if (button_pressed === 'private') {
        public.classList.remove('btn-success');
        public.classList.add('btn-outline-success');
        private.classList.remove('btn-outline-info');
        private.classList.add('btn-info');
        document.querySelector('#playlist_reach').dataset.playlist_reach = 'private';

    } else if(button_pressed === 'public') {
        private.classList.remove('btn-info');
        private.classList.add('btn-outline-info');
        public.classList.remove('btn-outline-success');
        public.classList.add('btn-success');
        document.querySelector('#playlist_reach').dataset.playlist_reach = 'public';
    }
}