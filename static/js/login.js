function validateForm() {
    const clienteId = document.getElementById('cliente_id').value.trim();
    const clienteIdError = document.getElementById('clienteIdError');

    if (!clienteId) {
        clienteIdError.style.display = 'block';
        clienteIdError.textContent = "Por favor, ingresa tu número de cliente.";
        return false;
    } else {
        clienteIdError.style.display = 'none';
        return true;
    }
}
