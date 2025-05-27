document.addEventListener('DOMContentLoaded', () => {
    const headlinesContainer = document.getElementById('headlines-container');
    const tabButtons = document.querySelectorAll('.tab-button');

    let headlines = []; // Initialize as empty, will be populated by fetch
    let currentTab = 'liked'; // Default active tab, updated to match HTML

    // --- Swipe variables ---
    let isSwiping = false;
    let startX = 0;
    let currentTranslate = 0;
    let activeHeadlineItem = null;
    const SWIPE_THRESHOLD_PERCENTAGE = 0.3; // 30% of page width

    // Function to render headlines based on the current tab
    function renderHeadlines() {
        headlinesContainer.innerHTML = ''; // Clear existing headlines

        const filteredHeadlines = headlines.filter(headline => {
            if (currentTab === 'all') {
                return true; // Show all headlines, including those with null status
            } else if (currentTab === 'liked') {
                return headline.status === 1; // Show liked (status 1)
            } else if (currentTab === 'disliked') {
                return headline.status === 0; // Show disliked (status 0)
            }
            return false; // Should not happen if currentTab is one of the three
        });

        if (filteredHeadlines.length === 0) {
            headlinesContainer.innerHTML = '<p>No headlines in this category yet.</p>';
            return;
        }

        filteredHeadlines.forEach(headline => {
            const headlineItem = document.createElement('div');
            headlineItem.classList.add('headline-item');
            headlineItem.dataset.id = headline.id; // Add data-id for swipe handling

            // Determine classes for buttons based on headline status
            let dislikeClass = '';
            let likeClass = '';

            if (headline.status === 0) { // Disliked
                dislikeClass = 'dislike';
            } else if (headline.status === 1) { // Liked
                likeClass = 'like';
            }

            headlineItem.innerHTML = `
                <div class="action-buttons">
                    <button class="action-button ${dislikeClass}" data-id="${headline.id}" data-action="0">X</button>
                    <button class="action-button ${likeClass}" data-id="${headline.id}" data-action="1">&#10003;</button>
                </div>
                <a href="${headline.url}" target="_blank">${headline.title}</a>
            `;
            headlinesContainer.appendChild(headlineItem);
        });

        // Add event listeners to the new buttons
        addActionButtonListeners();
        // Add swipe listeners to all headline items
        addSwipeListeners();
    }

    // Function to handle like/dislike actions
    async function handleAction(id, action) { // action will be 0 or 1 (integer)
        const newStatus = action; // Already an integer
        const headlineIndex = headlines.findIndex(h => h.id === id);
        if (headlineIndex > -1) {
            // Update the status of the headline locally first for immediate visual feedback
            headlines[headlineIndex].status = newStatus;
            renderHeadlines(); // Re-render headlines to reflect the change immediately

            // Now, send this update to the server for persistence
            try {
                const response = await fetch(`/api/headlines/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ status: newStatus }), // Send integer status
                });

                if (!response.ok) {
                    // If server update fails, log an error.
                    // In a more robust app, you might revert the local change or show a user-facing error.
                    console.error(`Failed to update headline ${id} on server: ${response.statusText}`);
                } else {
                    console.log(`Headline ${id} status updated to ${newStatus} on server.`);
                }
            } catch (error) {
                console.error('Error sending update to server:', error);
            }
        }
    }

    // Function to attach event listeners to action buttons
    function addActionButtonListeners() {
        document.querySelectorAll('.action-button').forEach(button => {
            button.onclick = (event) => {
                // Prevent swipe logic from interfering with button clicks
                // If a swipe just ended, don't process as click
                if (isSwiping) {
                    isSwiping = false; // Reset flag
                    return;
                }
                const id = parseInt(event.target.dataset.id);
                const action = parseInt(event.target.dataset.action); // Parse to int
                handleAction(id, action);
            };
        });
    }

    // --- Swipe Handlers ---
    function addSwipeListeners() {
        document.querySelectorAll('.headline-item').forEach(item => {
            item.addEventListener('pointerdown', handlePointerDown);
        });
    }

    function handlePointerDown(event) {
        // Only start swipe if it's a primary button (left click or touch)
        if (event.button !== 0 && event.pointerType !== 'touch') return;

        // If the click originated from an action button, don't start swipe
        if (event.target.closest('.action-button')) {
            return;
        }

        isSwiping = false; // Reset swipe flag
        activeHeadlineItem = event.currentTarget;
        startX = event.clientX || event.touches[0].clientX; // For mouse or touch
        activeHeadlineItem.style.transition = 'none'; // Disable transition during swipe

        document.addEventListener('pointermove', handlePointerMove);
        document.addEventListener('pointerup', handlePointerUp);
        document.addEventListener('pointercancel', handlePointerUp); // For when touch is interrupted
    }

    function handlePointerMove(event) {
        if (!activeHeadlineItem) return;

        const currentX = event.clientX || event.touches[0].clientX;
        currentTranslate = currentX - startX;

        // Only consider it a swipe if horizontal movement is significant
        // and prevent vertical scrolling if it's a horizontal swipe
        if (Math.abs(currentTranslate) > 5) { // Small threshold to differentiate from a tap
            isSwiping = true;
            event.preventDefault(); // Prevent scrolling
            activeHeadlineItem.style.transform = `translateX(${currentTranslate}px)`;
        }
    }

    function handlePointerUp(event) {
        if (!activeHeadlineItem) return;

        activeHeadlineItem.style.transition = 'transform 0.3s ease-out'; // Re-enable transition
        activeHeadlineItem.style.transform = 'translateX(0)'; // Reset position

        document.removeEventListener('pointermove', handlePointerMove);
        document.removeEventListener('pointerup', handlePointerUp);
        document.removeEventListener('pointercancel', handlePointerUp);

        if (isSwiping) {
            const swipeDistance = currentTranslate;
            const pageWidth = window.innerWidth;
            const swipeThresholdPx = pageWidth * SWIPE_THRESHOLD_PERCENTAGE;
            const headlineId = parseInt(activeHeadlineItem.dataset.id);

            if (swipeDistance > swipeThresholdPx) {
                // Swiped right (liked)
                handleAction(headlineId, 1);
            } else if (swipeDistance < -swipeThresholdPx) {
                // Swiped left (disliked)
                handleAction(headlineId, 0);
            }
            // Reset isSwiping flag after processing
            isSwiping = false;
        }

        activeHeadlineItem = null;
        startX = 0;
        currentTranslate = 0;
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
    fetch('/api/headlines')
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
