// Agregar evento de entrada a cada campo para validar individualmente
document.querySelectorAll('.register__input').forEach(input => {
    input.addEventListener('input', function () {
        validateSingleField(input); // Validar solo el campo que se está editando
    });

    input.addEventListener('focus', function () {
        clearErrorMessages(); // Limpiar todos los mensajes de error al enfocar
    });
});

function validateSingleField(input) {
    const fieldId = input.id;
    const value = input.value.trim();
    let isValid = true;
    let errorMessage = "";

    // Validación según el campo
    switch (fieldId) {
        case 'nombre':
            if (!/^[a-zA-Z\s]{4,}$/.test(value)) {
                errorMessage = "El nombre debe tener al menos 4 letras.";
                isValid = false;
            }
            break;
        case 'contraseña':
            if (!/^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]{6,}$/.test(value)) {
                errorMessage = "La contraseña debe tener al menos 6 caracteres, con letras y números.";
                isValid = false;
            }
            break;
        case 'rut':
            if (!validarRut(value)) {
                errorMessage = "El RUT es incorrecto. Debe ser sin puntos y con guion.";
                isValid = false;
            }
            break;
        case 'correo':
            if (!/^\S+@\S+\.\S+$/.test(value)) {
                errorMessage = "El correo electrónico no es válido.";
                isValid = false;
            }
            break;
        case 'direccion':
            if (!/^[a-zA-Z0-9\s]+$/.test(value)) {
                errorMessage = "La dirección solo puede contener letras y números.";
                isValid = false;
            }
            break;
        case 'telefono':
            if (!/^\+56\d{9}$/.test(value)) {
                errorMessage = "El número de teléfono debe tener el formato +56 seguido de 9 dígitos.";
                isValid = false;
            }
            break;
    }

    // Mostrar o ocultar el mensaje de error
    const errorElement = document.getElementById(`${fieldId}Error`);
    if (!isValid) {
        errorElement.innerText = errorMessage;
        errorElement.style.display = 'block';
    } else {
        errorElement.style.display = 'none';
    }

    // Validar el formulario completo
    validateForm();
}

function validateForm() {
    const inputs = document.querySelectorAll('.register__input');
    let isValid = true;

    inputs.forEach(input => {
        if (input.style.display !== 'none') { // Solo validar campos visibles
            const errorElement = document.getElementById(`${input.id}Error`);
            if (errorElement.style.display === 'block') {
                isValid = false;
            }
        }
    });

    // Habilitar o deshabilitar el botón de registro
    document.getElementById('registerBtn').disabled = !isValid;

    return isValid;
}



// Función para validar RUT de Chile
function validarRut(rut) {
    if (!/^[0-9]+-[0-9kK]{1}$/.test(rut)) return false;
    
    const [num, dig] = rut.split('-');
    const suma = [...num].reverse().reduce((acc, d, i) => acc + d * ((i % 6) + 2), 0);
    const dv = (11 - (suma % 11)) % 11;
    return (dv == dig.toLowerCase() || (dv == 10 && dig.toLowerCase() == 'k'));
}
