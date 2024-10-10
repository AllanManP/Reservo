let currentSlide = 0;
const slides = document.querySelectorAll('.carousel-item');
const indicatorsContainer = document.querySelector('.carousel-indicators');
const totalSlides = slides.length;
const slideInterval = 2000; // Intervalo de 2 segundos

function createIndicators() {
    slides.forEach((_, index) => {
        const indicator = document.createElement('div');
        indicator.classList.add('carousel-indicator');
        indicator.addEventListener('click', () => goToSlide(index));
        indicatorsContainer.appendChild(indicator);
    });
}

function updateSlidePosition() {
    slides.forEach((slide, index) => {
        slide.classList.remove('active');
        if (index === currentSlide) {
            slide.classList.add('active');
        }
    });
    updateIndicators();
}

function updateIndicators() {
    const indicators = document.querySelectorAll('.carousel-indicator');
    indicators.forEach((indicator, index) => {
        indicator.classList.toggle('active', index === currentSlide);
    });
}

function nextSlide() {
    currentSlide = (currentSlide + 1) % totalSlides;
    updateSlidePosition();
}

function prevSlide() {
    currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
    updateSlidePosition();
}

function goToSlide(index) {
    currentSlide = index;
    updateSlidePosition();
}

// Cambia automáticamente cada 2 segundos
setInterval(nextSlide, slideInterval);

document.addEventListener('DOMContentLoaded', () => {
    createIndicators();
    updateSlidePosition();
});
