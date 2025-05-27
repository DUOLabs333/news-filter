from flask import Flask, render_template, jsonify, send_from_directory, request
import json
import os

app = Flask(__name__)

# Define the path to the headlines.json file
HEADLINES_FILE = 'headlines.json'

# Helper function to read headlines
def read_headlines():
    if os.path.exists(HEADLINES_FILE):
        with open(HEADLINES_FILE, 'r') as f:
            return json.load(f)
    return []

# Helper function to write headlines
def write_headlines(data):
    with open(HEADLINES_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get headlines
@app.route('/api/headlines')
def get_headlines():
    headlines_data = read_headlines()
    if headlines_data is not None:
        return jsonify(headlines_data)
    else:
        return jsonify({"error": "Headlines data not found"}), 404

# API endpoint to update a headline's status
@app.route('/api/headlines/<int:headline_id>', methods=['PUT'])
def update_headline_status(headline_id):
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({"error": "Invalid request data"}), 400

    new_status = data['status']
    headlines_data = read_headlines()

    found = False
    for headline in headlines_data:
        if headline['id'] == headline_id:
            headline['status'] = new_status
            found = True
            break

    if found:
        write_headlines(headlines_data)
        return jsonify({"message": "Headline status updated successfully"}), 200
    else:
        return jsonify({"error": "Headline not found"}), 404

if __name__ == '__main__':
    # Ensure the headlines.json file exists for initial run
    if not os.path.exists(HEADLINES_FILE):
        with open(HEADLINES_FILE, 'w') as f:
            json.dump([], f, indent=4)

    app.run(debug=True) # debug=True allows auto-reloading and provides helpful error messages
