document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('#product-search');
    const counter = document.querySelector('#product-search-count');
    const emptyState = document.querySelector('#product-search-empty');
    const cards = Array.from(document.querySelectorAll('.product-card'));
    const hideTimers = new WeakMap();

    if (!searchInput || !counter || !emptyState || cards.length === 0) {
        return;
    }

    const normalize = (value) => (
        String(value || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLocaleLowerCase('es')
            .trim()
    );

    const updateCount = (visibleCount) => {
        counter.textContent = `${visibleCount} ${visibleCount === 1 ? 'producto encontrado' : 'productos encontrados'}`;
        emptyState.hidden = visibleCount !== 0;
    };

    const showCard = (card) => {
        clearTimeout(hideTimers.get(card));
        card.hidden = false;
        requestAnimationFrame(() => card.classList.remove('is-filtered-out'));
    };

    const hideCard = (card) => {
        card.classList.add('is-filtered-out');
        clearTimeout(hideTimers.get(card));
        hideTimers.set(card, setTimeout(() => {
            if (card.classList.contains('is-filtered-out')) {
                card.hidden = true;
            }
        }, 140));
    };

    const filterProducts = () => {
        const query = normalize(searchInput.value);
        let visibleCount = 0;

        cards.forEach((card) => {
            const searchableText = normalize([
                card.dataset.name,
                card.dataset.category,
                card.dataset.description,
            ].join(' '));
            const matches = !query || searchableText.includes(query);

            if (matches) {
                visibleCount += 1;
                showCard(card);
            } else {
                hideCard(card);
            }
        });

        updateCount(visibleCount);
    };

    searchInput.addEventListener('input', filterProducts);
    filterProducts();
});
