from flask import Flask, render_template, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

# Define the path to the headlines.json file
HEADLINES_FILE = 'headlines.json'

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get headlines
@app.route('/api/headlines')
def get_headlines():
    if os.path.exists(HEADLINES_FILE):
        with open(HEADLINES_FILE, 'r') as f:
            headlines_data = json.load(f)
        return jsonify(headlines_data)
    else:
        return jsonify({"error": "Headlines data not found"}), 404

if __name__ == '__main__':
    # Ensure the headlines.json file exists for initial run
    if not os.path.exists(HEADLINES_FILE):
        initial_headlines = [
            { "id": 1, "title": "The Future of WebAssembly", "url": "https://example.com/wasm", "status": "liked" },
            { "id": 2, "title": "Building a SPA with Vanilla JS", "url": "https://example.com/vanilla-js", "status": "disliked" },
            { "id": 3, "title": "Why Rust is Gaining Popularity", "url": "https://example.com/rust", "status": "all" },
            { "id": 4, "title": "Understanding Async/Await in JavaScript", "url": "https://example.com/async-await", "status": "all" },
            { "id": 5, "title": "A Deep Dive into CSS Grid", "url": "https://example.com/css-grid", "status": "all" },
            { "id": 6, "title": "My Journey into Open Source", "url": "https://example.com/open-source", "status": "all" },
        ]
        with open(HEADLINES_FILE, 'w') as f:
            json.dump(initial_headlines, f, indent=4)
        print(f"Created initial {HEADLINES_FILE}")

    app.run(debug=True) # debug=True allows auto-reloading and provides helpful error messages
