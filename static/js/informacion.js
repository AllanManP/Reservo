document.addEventListener('DOMContentLoaded', () => {
    const infoSection = document.querySelector('#information');

    const observerOptions = {
        root: null, // Observa en relación al viewport
        rootMargin: '0px',
        threshold: 0.5 // Cuando el 10% de la sección está visible
    };

    const observerCallback = (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            } else {
                entry.target.classList.remove('visible');
            }
        });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);
    observer.observe(infoSection);
});
