from flask import Flask, render_template, jsonify, request
import json
import os

app = Flask(__name__)

"""
IMPORTANT NOTES (do not touch):
Function to write api results to headlines files with classification. Cached for 3 hours

Liked and disliked tabs retrieve based on classification

all_headlines should be sorted, so swiping doesn't change the final result.
"""
# Define the paths to the headline files
HEADLINES_FILE = 'headlines.json'
LIKED_HEADLINES_FILE = 'liked.json'
DISLIKED_HEADLINES_FILE = 'disliked.json'

# Helper function to read a specific JSON file
def _read_json_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {filepath} is empty or malformed. Returning empty list.")
                return []
    return []

# Helper function to write to a specific JSON file
def _write_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# Load all headlines from all three files
def load_all_headlines_data():
    unclassified = _read_json_file(HEADLINES_FILE)
    liked = _read_json_file(LIKED_HEADLINES_FILE)
    disliked = _read_json_file(DISLIKED_HEADLINES_FILE)
    return unclassified, liked, disliked

# Save all headlines to their respective files
def save_all_headlines_data(unclassified, liked, disliked):
    _write_json_file(HEADLINES_FILE, unclassified)
    _write_json_file(LIKED_HEADLINES_FILE, liked)
    _write_json_file(DISLIKED_HEADLINES_FILE, disliked)

# Function to find and remove a headline from any of the lists
def find_and_remove_headline(headline_id, unclassified, liked, disliked):
    for i, h in enumerate(unclassified):
        if h['id'] == headline_id:
            return unclassified.pop(i)
    for i, h in enumerate(liked):
        if h['id'] == headline_id:
            return liked.pop(i)
    for i, h in enumerate(disliked):
        if h['id'] == headline_id:
            return disliked.pop(i)
    return None

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get headlines for a specific tab
@app.route('/api/headlines/<tab_name>')
def get_headlines_by_tab(tab_name):
    unclassified, liked, disliked = load_all_headlines_data()
    
    if tab_name == 'all':
        # Combine all, adding status for client-side filtering/display
        all_headlines = []
        for h in unclassified:
            all_headlines.append({**h, 'status': None}) # Unclassified
        for h in liked:
            all_headlines.append({**h, 'status': 1}) # Liked
        for h in disliked:
            all_headlines.append({**h, 'status': 0}) # Disliked
        return jsonify(all_headlines)
    elif tab_name == 'liked':
        # Add status 1 to all liked headlines for consistency with frontend
        return jsonify([{**h, 'status': 1} for h in liked])
    elif tab_name == 'disliked':
        # Add status 0 to all disliked headlines for consistency with frontend
        return jsonify([{**h, 'status': 0} for h in disliked])
    else:
        return jsonify({"error": "Invalid tab name"}), 400

# API endpoint to like a headline
@app.route('/api/headlines/<int:headline_id>/like', methods=['PUT'])
def like_headline(headline_id):
    unclassified, liked, disliked = load_all_headlines_data()
    headline_to_move = find_and_remove_headline(headline_id, unclassified, liked, disliked)

    if headline_to_move:
        # Remove 'status' field if it exists, as presence in liked.json implies status 1
        if 'status' in headline_to_move:
            del headline_to_move['status']
        liked.append(headline_to_move)
        save_all_headlines_data(unclassified, liked, disliked)
        return jsonify({"message": "Headline liked successfully"}), 200
    else:
        return jsonify({"error": "Headline not found"}), 404

# API endpoint to dislike a headline
@app.route('/api/headlines/<int:headline_id>/dislike', methods=['PUT'])
def dislike_headline(headline_id):
    unclassified, liked, disliked = load_all_headlines_data()
    headline_to_move = find_and_remove_headline(headline_id, unclassified, liked, disliked)

    if headline_to_move:
        # Remove 'status' field if it exists, as presence in disliked.json implies status 0
        if 'status' in headline_to_move:
            del headline_to_move['status']
        disliked.append(headline_to_move)
        save_all_headlines_data(unclassified, liked, disliked)
        return jsonify({"message": "Headline disliked successfully"}), 200
    else:
        return jsonify({"error": "Headline not found"}), 404

if __name__ == '__main__':
    # Ensure all three JSON files exist for initial run
    for f in [HEADLINES_FILE, LIKED_HEADLINES_FILE, DISLIKED_HEADLINES_FILE]:
        if not os.path.exists(f):
            with open(f, 'w') as fp:
                json.dump([], fp, indent=4)

    # Migration logic: Move existing headlines with status from headlines.json to new files
    # This should only run once if headlines.json contains status fields
    initial_headlines = _read_json_file(HEADLINES_FILE)
    
    # Check if migration is needed (i.e., if headlines.json contains 'status' fields)
    if initial_headlines and any('status' in h for h in initial_headlines):
        print("Migrating existing headlines from headlines.json to separate files...")
        
        unclassified_migrated = []
        liked_migrated = _read_json_file(LIKED_HEADLINES_FILE)
        disliked_migrated = _read_json_file(DISLIKED_HEADLINES_FILE)

        for headline in initial_headlines:
            # Create a copy to modify without affecting iteration
            headline_copy = headline.copy() 
            
            if headline_copy.get('status') == 1:
                if 'status' in headline_copy: del headline_copy['status']
                liked_migrated.append(headline_copy)
            elif headline_copy.get('status') == 0:
                if 'status' in headline_copy: del headline_copy['status']
                disliked_migrated.append(headline_copy)
            else: # status is None or not present
                if 'status' in headline_copy: del headline_copy['status'] # Remove status if it was null
                unclassified_migrated.append(headline_copy)
        
        save_all_headlines_data(unclassified_migrated, liked_migrated, disliked_migrated)
        print("Migration complete. Original headlines.json content has been distributed.")
    
    app.run(debug=True) # debug=True allows auto-reloading and provides helpful error messages
