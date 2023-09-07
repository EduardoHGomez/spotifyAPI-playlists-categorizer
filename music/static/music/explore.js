let tags = [];

document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#filter-form').onsubmit = event => {
        event.preventDefault();
        addTag();
    };
})


function addTag() {
    // Add text and clean input space
    text = document.querySelector('#input_tags').value;
    document.querySelector('#input_tags').value = '';
    if (text === '' || tags.includes(text)) {
        return false;
    }

    // Append to array
    tags.push(text);

    // Create new element and add to filters
    filters = document.querySelector('.filters');
    filters.style.display = 'flex';

    new_tag = document.createElement('span');    
    new_tag.innerHTML = `${text}<a href="javascript:deleteTag('${text}')"> x </a>`;
    new_tag.setAttribute('id', `tag_${text}`);

    // Append to 'filters' div
    filters.append(new_tag);

    showFiltered();
    return false;
}

function deleteTag(category) {
    // Delete span element
    to_delete = document.querySelector(`#tag_${category}`);
    to_delete.remove();

    // Delete from Array
    index = tags.indexOf(category);
    tags.splice(index, 1);

    document.querySelector('.playlists').innerHTML = '';
    showFiltered();

}

function showFiltered() {
    playlist_content = document.querySelector('.playlists');
    playlist_content.style.display = 'flex';

    fetch(`/show-playlists-filtered?tags=${tags}`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        playlists = data.playlists;
        playlists.forEach(playlist => {
                // Before creating new card, check if the playlist already exists                
                console.log(playlist.tags);
                const playlist_exists = document.querySelector(`#playlist_${playlist.id}`);

                if (playlist_exists == null) {
                    // Create new card
                    card = document.createElement('div');
                    card.classList.add('card');
                    card.setAttribute('id', `playlist_${playlist.id}`)
                    card.style.width = '18rem';
                    card.innerHTML = `
                    <div class="card-body">
                        <img class="card-img-top" src="${playlist.image}"></img>
                        <h5 class="card-title"><a href="playlist/${playlist.playlist_id}">${playlist.name}</a></h5>
                        <p class="card-text">${playlist.description}</p>
                    </div>
                    `
                    tags_div = document.createElement('div');
                    tags_div.classList.add('playlist_tags_span');

                    playlist.tags.forEach(tag => {
                        new_tag = document.createElement('span');
                        new_tag.innerHTML = `
                            <a href="explore/${tag}">${tag}</a>
                        `;
                        tags_div.append(new_tag);
                    });

                    playlist_content.append(card);
                    
                    current_body = playlist_content.querySelector(`#playlist_${playlist.id}`);
                    current_body = current_body.querySelector('.card-body');
                    current_body.append(tags_div);

                    color1 = playlist.background_color;
                    color2 = playlist.secondary_color; 

                    color1 += 'bd';
                    color2 += 'bd';
                    // Set backgroudn color to default
                    card.style.backgroundColor = 'white';

                    // Change background linear with JavaScript
                    card.style.backgroundImage = 
                    "linear-gradient(to top, "+ color1 +", "+ color2 +")";

                }

        });
    });
}