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