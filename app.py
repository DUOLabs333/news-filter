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
        with open(HEADLINES_FILE, 'w') as f:
            json.dump([], f, indent=4)

    app.run(debug=True) # debug=True allows auto-reloading and provides helpful error messages
