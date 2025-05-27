document.addEventListener('DOMContentLoaded', () => {
    const headlinesContainer = document.getElementById('headlines-container');
    const tabButtons = document.querySelectorAll('.tab-button');

    // Dummy data for Hacker News headlines
    // In a real app, you'd fetch this from an API
    let headlines = [
        { id: 1, title: 'The Future of WebAssembly', url: 'https://example.com/wasm', status: 'all' },
        { id: 2, title: 'Building a SPA with Vanilla JS', url: 'https://example.com/vanilla-js', status: 'all' },
        { id: 3, title: 'Why Rust is Gaining Popularity', url: 'https://example.com/rust', status: 'all' },
        { id: 4, title: 'Understanding Async/Await in JavaScript', url: 'https://example.com/async-await', status: 'all' },
        { id: 5, title: 'A Deep Dive into CSS Grid', url: 'https://example.com/css-grid', status: 'all' },
        { id: 6, title: 'My Journey into Open Source', url: 'https://example.com/open-source', status: 'all' },
    ];

    let currentTab = 'all'; // Default active tab

    // Function to render headlines based on the current tab
    function renderHeadlines() {
        headlinesContainer.innerHTML = ''; // Clear existing headlines

        const filteredHeadlines = headlines.filter(headline => {
            if (currentTab === 'all') {
                return true; // Show all headlines
            }
            return headline.status === currentTab; // Show liked or disliked
        });

        if (filteredHeadlines.length === 0) {
            headlinesContainer.innerHTML = '<p>No headlines in this category yet.</p>';
            return;
        }

        filteredHeadlines.forEach(headline => {
            const headlineItem = document.createElement('div');
            headlineItem.classList.add('headline-item');

            headlineItem.innerHTML = `
                <div class="action-buttons">
                    <button class="action-button dislike" data-id="${headline.id}" data-action="dislike">X</button>
                    <button class="action-button like" data-id="${headline.id}" data-action="like">&#10003;</button>
                </div>
                <a href="${headline.url}" target="_blank">${headline.title}</a>
            `;
            headlinesContainer.appendChild(headlineItem);
        });

        // Add event listeners to the new buttons
        addActionButtonListeners();
    }

    // Function to handle like/dislike actions
    function handleAction(id, action) {
        const headlineIndex = headlines.findIndex(h => h.id === id);
        if (headlineIndex > -1) {
            // Update the status of the headline
            headlines[headlineIndex].status = action;
            // Re-render headlines to reflect the change
            renderHeadlines();
        }
    }

    // Function to attach event listeners to action buttons
    function addActionButtonListeners() {
        document.querySelectorAll('.action-button').forEach(button => {
            button.onclick = (event) => {
                const id = parseInt(event.target.dataset.id);
                const action = event.target.dataset.action;
                handleAction(id, action);
            };
        });
    }

    // Event listeners for tab buttons
    tabButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            // Remove 'active' class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));

            // Add 'active' class to the clicked button
            event.target.classList.add('active');

            // Update current tab and re-render
            currentTab = event.target.dataset.tab;
            renderHeadlines();
        });
    });

    // Initial render when the page loads
    renderHeadlines();
});
