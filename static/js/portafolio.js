function verMas(index) {
    const modal = document.getElementById(`modal-${index}`);
    modal.style.display = "block";
}

function cerrarModal(index) {
    const modal = document.getElementById(`modal-${index}`);
    modal.style.display = "none";
}

// Cerrar el modal al hacer clic fuera del contenido
window.onclick = function(event) {
    const modals = document.querySelectorAll(".modal");
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
};
