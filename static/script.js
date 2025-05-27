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
    let activeHeadlineContent = null; // New: Reference to the content div
    let activeSwipeBackground = null; // New: Reference to the swipe background div
    const SWIPE_THRESHOLD_PERCENTAGE = 0.2; // 20% of page width for action
    const SWIPE_VISUAL_THRESHOLD_PX = 50; // Pixels to show visual feedback

    // Function to render headlines based on the current tab
    function renderHeadlines() {
        headlinesContainer.innerHTML = ''; // Clear existing headlines

        // No client-side filtering needed here, as the backend will provide filtered data
        // based on the fetch call.
        if (headlines.length === 0) {
            headlinesContainer.innerHTML = '<p>No headlines in this category yet.</p>';
            return;
        }

	for (const id in headlines){
		headline=headlines[id];
		const headlineItem = document.createElement('div');
	    	headlineItem.classList.add('headline-item');
	    	headlineItem.dataset.id = id; // Add data-id for swipe handling

		// Determine classes for buttons based on headline status
		let dislikeClass = '';
		let likeClass = '';

	    	// The backend will now explicitly add 'status' to all returned headlines
	    	if (headline.status === 0) { // Disliked
			dislikeClass = 'dislike';
		} else if (headline.status === 1) { // Liked
			likeClass = 'like';
		}

	    // New HTML structure for swipe feedback
	    headlineItem.innerHTML = `
		<div class="swipe-background">
		    <span class="swipe-icon swipe-icon-left">&#10003;</span>
		    <span class="swipe-icon swipe-icon-right">X</span>
		</div>
		<div class="headline-content">
		    <div class="action-buttons">
			<button class="action-button ${dislikeClass}" data-id="${id}" data-action="dislike">X</button>
			<button class="action-button ${likeClass}" data-id="${id}" data-action="like">&#10003;</button>
		    </div>
		    <a href="${headline.url}" target="_blank">${headline.title}</a>
		</div>
	    `;
	    headlinesContainer.appendChild(headlineItem);
	}

        // Add event listeners to the new buttons
        addActionButtonListeners();
        // Add swipe listeners to all headline items
        addSwipeListeners();
    }

    // Function to handle like/dislike actions
    async function handleAction(id, action) { // action will be 0 or 1 (integer)
        // Optimistically update UI first: remove the headline from the current client-side list

		if (currentTab!= "all"){
			delete headlines[id];
		}
		renderHeadlines(); //Re-render to show immediate removal

		try {
		    const response = await fetch(`/api/headlines/${id}/${action}`, {
			method: 'GET',
			headers: {
			    'Content-Type': 'application/json',
			},
		    });

		    if (!response.ok) {
			console.error(`Failed to update headline ${id} on server: ${response.statusText}`);
			// If server update fails, re-fetch to revert UI to actual state
			fetchHeadlinesForCurrentTab();
		    } else {
			console.log(`Headline ${id} moved to ${action} on server.`);
			// After successful action, re-fetch headlines for the current tab
			// to ensure the list is up-to-date and reflects the change.
			//fetchHeadlinesForCurrentTab();
		    }
		} catch (error) {
		    console.error('Error sending update to server:', error);
		    // If network error, re-fetch to revert UI to actual state
		    fetchHeadlinesForCurrentTab();
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
                handleAction(event.target.dataset.id, event.target.dataset.action);
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
        activeHeadlineContent = activeHeadlineItem.querySelector('.headline-content');
        activeSwipeBackground = activeHeadlineItem.querySelector('.swipe-background');

        startX = event.clientX || (event.touches && event.touches[0] ? event.touches[0].clientX : event.clientX); // For mouse or touch
        activeHeadlineContent.style.transition = 'none'; // Disable transition during swipe

        document.addEventListener('pointermove', handlePointerMove);
        document.addEventListener('pointerup', handlePointerUp);
        document.addEventListener('pointercancel', handlePointerUp); // For when touch is interrupted
    }

    function handlePointerMove(event) {
        if (!activeHeadlineItem || !activeHeadlineContent || !activeSwipeBackground) return;

        const currentX = event.clientX || (event.touches && event.touches[0] ? event.touches[0].clientX : event.clientX);
        currentTranslate = currentX - startX;

        // Only consider it a swipe if horizontal movement is significant
        // and prevent vertical scrolling if it's a horizontal swipe
        if (Math.abs(currentTranslate) > 5) { // Small threshold to differentiate from a tap
            isSwiping = true;
            event.preventDefault(); // Prevent scrolling
            activeHeadlineContent.style.transform = `translateX(${currentTranslate}px)`;

            // Visual feedback logic
            if (Math.abs(currentTranslate) > SWIPE_VISUAL_THRESHOLD_PX) {
                if (currentTranslate > 0) { // Swiping right
                    activeSwipeBackground.classList.add('like');
                    activeSwipeBackground.classList.remove('dislike');
                } else { // Swiping left
                    activeSwipeBackground.classList.add('dislike');
                    activeSwipeBackground.classList.remove('like');
                }
            } else {
                // If swipe is not significant enough for visual feedback, reset
                activeSwipeBackground.classList.remove('like', 'dislike');
            }
        }
    }

    function handlePointerUp(event) {
        if (!activeHeadlineItem || !activeHeadlineContent || !activeSwipeBackground) return;

        activeHeadlineContent.style.transition = 'transform 0.3s ease-out'; // Re-enable transition
        activeHeadlineContent.style.transform = 'translateX(0)'; // Reset position

        // Reset swipe background classes
        activeSwipeBackground.classList.remove('like', 'dislike');

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
        activeHeadlineContent = null;
        activeSwipeBackground = null;
        startX = 0;
        currentTranslate = 0;
    }

    // New function to fetch headlines based on current tab
    async function fetchHeadlinesForCurrentTab() {
        try {
            const response = await fetch(`/api/headlines/${currentTab}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            headlines = data; // Update global headlines array
            renderHeadlines(); // Re-render with new data
        } catch (error) {
            console.error('Error fetching headlines:', error);
            headlinesContainer.innerHTML = '<p>Failed to load headlines. Please try again later.</p>';
        }
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
            fetchHeadlinesForCurrentTab(); // Fetch new data when tab changes
        });
    });

    // Initial fetch when DOM is loaded
    fetchHeadlinesForCurrentTab();
});
