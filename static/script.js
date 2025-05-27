document.addEventListener('DOMContentLoaded', () => {
    const headlinesContainer = document.getElementById('headlines-container');
    const tabButtons = document.querySelectorAll('.tab-button');

    let headlines = []; // Initialize as empty, will be populated by fetch
    let currentTab = 'liked'; // Default active tab, updated to match HTML

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

            // Determine classes for buttons based on headline status
            let dislikeClass = '';
            let likeClass = '';

            if (headline.status === 'disliked') {
                dislikeClass = 'dislike';
            } else if (headline.status === 'liked') {
                likeClass = 'like';
            }

            headlineItem.innerHTML = `
                <div class="action-buttons">
                    <button class="action-button ${dislikeClass}" data-id="${headline.id}" data-action="dislike">X</button>
                    <button class="action-button ${likeClass}" data-id="${headline.id}" data-action="like">&#10003;</button>
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
            // TODO: In a real app, you'd send this update to the server
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

    // Fetch headlines from Flask API endpoint
    fetch('/api/headlines') // Changed URL to Flask endpoint
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            headlines = data; // Assign fetched data to headlines array
            renderHeadlines(); // Initial render after data is loaded
        })
        .catch(error => {
            console.error('Error fetching headlines:', error);
            headlinesContainer.innerHTML = '<p>Failed to load headlines. Please try again later.</p>';
        });
});
