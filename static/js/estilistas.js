// Variables del carrusel
let currentStylistIndex = 0;
const stylists = document.querySelectorAll('.carousel-item-stylist');
const stylistInput = document.getElementById('stylist');
const dots = document.querySelectorAll('.dot');

// Función para actualizar el carrusel y los indicadores
function showStylist(index) {
    stylists.forEach((stylist, i) => {
        stylist.classList.remove('active');
        if (i === index) {
            stylist.classList.add('active');
            // Actualizar el nombre del estilista en el formulario
            const selectedStylist = stylist.getAttribute('data-stylist');
            stylistInput.value = selectedStylist;
        }
    });

    // Actualizar los indicadores (dots)
    dots.forEach((dot, i) => {
        dot.classList.remove('active');
        if (i === index) {
            dot.classList.add('active');
        }
    });
}

// Función para cambiar al estilista anterior
function prevStylist() {
    currentStylistIndex = (currentStylistIndex === 0) ? stylists.length - 1 : currentStylistIndex - 1;
    showStylist(currentStylistIndex);
}

// Función para cambiar al siguiente estilista
function nextStylist() {
    currentStylistIndex = (currentStylistIndex === stylists.length - 1) ? 0 : currentStylistIndex + 1;
    showStylist(currentStylistIndex);
}

// Función para seleccionar estilista mediante los indicadores (dots)
function currentStylistIndicator(index) {
    currentStylistIndex = index;
    showStylist(currentStylistIndex);
}

// Inicialización: mostrar el primer estilista
showStylist(currentStylistIndex);


