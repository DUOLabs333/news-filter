# news-filter
Using LLMs to filter news sources from Hacker News, and optionally, Lobste.rs

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd news-filter
    ```

2.  **Install dependencies using PDM:**

    ```bash
    pdm install
    ```

3.  **Configure Environment Variables:**

    *   Create a `.env` file in the project root directory.
    *   Add your Google Gemini API key to the `.env` file:

        ```
        GEMINI_API_KEY=YOUR_GEMINI_API_KEY
        ```

## Usage

1.  **Run the Flask application:**

    ```bash
    pdm run flask run
    ```

2.  **Open the application in your web browser:**

    Navigate to `http://127.0.0.1:5000/` (or the address shown in the console output).


## How to use
	* Every hour, the server will ingest stories from the different aggregators and use a LLM to categorize them into "Liked" and "Disliked" categories.

	* Go to the "Liked" and "Disliked" tabs to read stories and/or vote on whether you liked or disliked them --- every vote gives more information to the LLM so it can make better decisions!
		* You can either swipe left or right to "like" or "dislike" a story respectively, or use the X and checkmark buttons.

		*  Click on a headline to open the aggregator url in a new tab.

    	* If you make a mistake, don't worry! Just go to the "All" tab to change your vote.

## Contributing

Contributions are highly welcome!  Please feel free to submit pull requests with bug fixes, new features, or improvements to the documentation.

	* I especially need help working on the UI and UX --- if you look at the JS and CSS files, it is clear I don't really know what I'm doing there. 
