document.addEventListener('DOMContentLoaded', function() {
    const calendar = document.getElementById('calendar');
    const timeSlots = document.getElementById('time-slots');
    const selectedDateInput = document.getElementById('selected-date');
    const selectedTimeInput = document.getElementById('selected-time');

    // Ejemplo de disponibilidad
    const availability = {
        "2024-09-22": ["09:00", "10:00", "14:00"],
        "2024-09-23": ["11:00", "15:00", "16:00"]
    };

    // Generar días del mes
    for (let i = 1; i <= 30; i++) {
        const dayDiv = document.createElement('div');
        dayDiv.classList.add('calendar-day');
        const date = `2024-09-${i < 10 ? '0' + i : i}`;
        dayDiv.innerText = i;

        if (availability[date]) {
            dayDiv.classList.add('available');
            dayDiv.addEventListener('click', function() {
                showAvailableTimes(date);
            });
        }

        calendar.appendChild(dayDiv);
    }

    function showAvailableTimes(date) {
        timeSlots.innerHTML = '';  // Limpiar los slots de tiempo
        selectedDateInput.value = date;  // Establecer la fecha seleccionada

        if (availability[date]) {
            availability[date].forEach(time => {
                const li = document.createElement('li');
                li.innerText = time;
                li.classList.add('available');
                li.addEventListener('click', function() {
                    selectTime(time);
                });
                timeSlots.appendChild(li);
            });
        }
    }

    function selectTime(time) {
        selectedTimeInput.value = time;  // Establecer la hora seleccionada
    }
});
