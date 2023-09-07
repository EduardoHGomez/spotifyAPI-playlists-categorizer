document.addEventListener('DOMContentLoaded', function() {
    setGradients();
});


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