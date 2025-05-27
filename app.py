from flask import Flask, render_template, jsonify, request
import os, signal, json, atexit

app = Flask(__name__)

"""
IMPORTANT NOTES (do not touch):
Function to write api results to headlines files with classification. Cached for 3 hours

Liked and disliked tabs retrieve based on classification

all_headlines should be sorted, so swiping doesn't change the final result.

id should be {domain}-{id}
"""

def write_file(data, path):
    with open(path+'1', 'w+') as f:
        json.dump(data, f, indent=4)
    os.rename(path+'1', path)

unsorted={}
liked={}
disliked={}

def save_all_files():
    write_file(unsorted, UNSORTED_FILE)
    write_file(liked, LIKED_FILE)
    write_file(disliked, DISLIKED_FILE)

signal_handlers={}

for signum in [signal.SIGTERM, signal.SIGINT]:
    def handler(signum, dummy):
        save_all_files()
        signal.signal(signum, signal_handlers[signum])
        signal.raise_signal(signum)
    signal_handlers[signum]=signal.signal(signum, handler)

atexit.register(save_all_files)

UNSORTED_FILE = 'unsorted.json'
LIKED_FILE = 'liked.json'
DISLIKED_FILE = 'disliked.json'

def read_file(path):
    with open(path, 'r+') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def sort(d):
    d_copy=dict(sorted(d.items(), reverse=True, key= lambda item: item[1]["time"]))
    d.clear()
    d.update(d_copy)
    
# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get headlines for a specific tab
@app.route('/api/headlines/<tab_name>')
def get_tab(tab_name):
    if tab_name == 'all':
        # Combine all, adding status for client-side filtering/display
        combined=liked|disliked
        sort(combined)
        return jsonify(combined)
    else:
        return jsonify(dict(filter(lambda item: item[1]["status"]==(0 if tab_name=="disliked" else 1), unsorted.items())))

# API endpoint to like a headline
@app.route('/api/headlines/<id>/<action>', methods=['GET'])
def action(id, action):

    status=(0 if action=="dislike" else 1)

    if unsorted.get(id):
        src=unsorted
    elif liked.get(id):
        src=liked
    else:
        src=disliked

    if action=="dislike":
        dst=disliked
    else:
        dst=liked

    dst[id]=src[id]
    dst[id]["status"]=status
    sort(dst)

    del src[id]
    
    if not(src is dst):
        save_all_files()

    return '', 200

unsorted = read_file(UNSORTED_FILE)
liked = read_file(LIKED_FILE)
disliked = read_file(DISLIKED_FILE)
