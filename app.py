from flask import Flask, render_template, jsonify
import os, signal, json, atexit, threading, contextlib, datetime

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

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
    os.replace(path+'1', path)


def save_all_files():
    write_file(unsorted, UNSORTED_FILE)
    write_file(liked, LIKED_FILE)
    write_file(disliked, DISLIKED_FILE)

def read_file(path):
    with open(path, 'r+') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def sort(d):
    def custom_key(item):
        domain=item[0]
        if domain.startswith("lobsters-"): #There are much less Lobsters stories per day compared to HN, and they are usually much higher quality (higher SNR), so they should be ranked first
            domain=1
        elif domain.startswith("hn-"):
            domain=0

        return (domain, item[1]["time"])
    d_copy=dict(sorted(d.items(), reverse=True, key= custom_key))
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

    if not(src is dst):
        with unsorted_lock if ((src is unsorted) or (dst is unsorted)) else contextlib.nullcontext():
            dst[id]=src[id]
            dst[id]["status"]=status
            sort(dst)
            del src[id]
            
            save_all_files()

    return '', 200

if not os.environ.get("RELOADER_HAS_RUN"): #Otherwise, the exit handlers will be set for both the reloader process and the actual application process, leading to files being overwritten twice.
    os.environ["RELOADER_HAS_RUN"]="1"
else:
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

    unsorted={}
    liked={}
    disliked={}

    unsorted_lock=threading.Lock() #This is meant for periodic updates to the unsorted dictionary

    unsorted = read_file(UNSORTED_FILE)
    liked = read_file(LIKED_FILE)
    disliked = read_file(DISLIKED_FILE)

    def update():
        result_main={}
        result_aux={}
        hn_stories=requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()
        
        with ThreadPoolExecutor(max_workers=10) as pool:
            while len(hn_stories)>0:
                futures={pool.submit(lambda id: requests.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json")) for id in hn_stories}

                hn_stories.clear()

                for future in as_completed(futures):
                    response=future.result()
                    if response.status_code!=200:
                        hn_stories.append(response.url)
                    else:
                        data=response.json()
                        id=f"hn-{data['id']}"
                        result_main[id]={"title": data["title"], "url": data.get("url", ""), "description": data.get("text", ""),  "tags": []}
                        
                        result_aux[id]={"post_url": f"https://news.ycombinator.com/item?id={data['id']}", "time": data["time"]}


        lobsters_stories=requests.get("https://lobste.rs/hottest.json").json()

        for story in lobsters_stories:
            pass #Disable Lobste.rs integration for now --- hottest only returns the first page, when in fact, I want more than the first page

            id=f"lobsters-{story['short_id']}"
            result_main[id]={"title": story["title"], "url": story["url"], "description": story["description_plain"], "tags": story["tags"]} 

            result_aux[id]={"post_url": story["short_id_url"], "time": int(datetime.datetime.fromisoformat(story["created_at"]).astimezone(datetime.UTC).timestamp())}



        


