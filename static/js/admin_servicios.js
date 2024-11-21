// Función para detectar cuándo los elementos entran en la vista
function handleScroll() {
    const serviceItems = document.querySelectorAll('.service-item');
    const windowHeight = window.innerHeight;

    serviceItems.forEach(item => {
        const itemTop = item.getBoundingClientRect().top;

        // Si el elemento está en la vista, añadir la clase 'visible'
        if (itemTop < windowHeight - 100) {
            item.classList.add('visible');
        }
    });
}

// Función para confirmar y eliminar el servicio
function eliminarServicio(id) {
    if (confirm("¿Estás seguro de que deseas eliminar este servicio?")) {
        // Lógica para eliminar el servicio usando el ID
        window.location.href = `/admin/servicios/eliminar/${id}`;
    }
}

// Función para redirigir a la página de edición del servicio
function modificarServicio(id) {
    // Lógica para editar el servicio usando el ID
    window.location.href = `/admin/servicios/modificar/${id}`;
}

// Función para alternar el acordeón y actualizar la imagen del servicio
function toggleAccordion(event, service) {
    const item = event.target.parentElement;

    // Cerrar otros items del acordeón
    const allItems = document.querySelectorAll('.accordion-item');
    allItems.forEach(i => {
        if (i !== item) {
            i.classList.remove('active');
            i.querySelector('.accordion-content').style.maxHeight = null;
        }
    });

    // Alternar el item clicado
    item.classList.toggle("active");
    const content = item.querySelector('.accordion-content');
    content.style.maxHeight = item.classList.contains("active") ? content.scrollHeight + "px" : null;

    // Actualizar la imagen del servicio
    const serviceImage = document.getElementById('service-image');
    let images = {
        balayage: "{{ url_for('static', filename='img/cortes/balayage.jpg') }}",
        babylight: "{{ url_for('static', filename='img/cortes/babylight.jpg') }}",
        cortes: "{{ url_for('static', filename='img/cortes/cortes.jpg') }}",
        color: "{{ url_for('static', filename='img/cortes/color.jpg') }}",
        canas: "{{ url_for('static', filename='img/cortes/canas.jpg') }}"
    };

    serviceImage.src = images[service];
    serviceImage.style.display = 'block';

    // Guardar el servicio seleccionado en el campo oculto
    document.getElementById('selected-service').value = service;
}

// Ejecutar la función cuando la página se carga y cuando el usuario hace scroll
window.addEventListener('scroll', handleScroll);
window.addEventListener('load', handleScroll);
