from flask import Flask, render_template, jsonify, g
import os, json, threading, datetime, sqlite3, time
from werkzeug.local import LocalProxy

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, dotenv

app = Flask(__name__)

config=dotenv.dotenv_values()

"""
IMPORTANT NOTES (do not touch):
Function to write api results to headlines files with classification. Cached for 3 hours

Liked and disliked tabs retrieve based on classification

all_headlines should be sorted, so swiping doesn't change the final result.

id should be {domain}-{id}
"""

DATABASE="db.db"
TABLE="main"

HISTORY_LIMIT=5_000
POOL_LIMIT=10
TAB_LIMIT=10 #How many items can be shown on a tab at any one time
GEMINI_MODEL="gemini-2.5-pro-preview-05-06"

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get headlines for a specific tab
# Add support for getting a specific limit and offset
@app.route('/api/headlines/<tab_name>')
def get_tab(tab_name):
    if tab_name == 'all':
        # Combine all, adding status for client-side filtering/display
        
        query="sorted_at is not null"
        sort="sorted_at desc"

    else:
        query=f"sorted_at is null and category = {'0' if tab_name=='disliked' else '1'}"
        sort="""
            CASE
                WHEN post_id LIKE 'lobsters-%' THEN 0
                WHEN post_id LIKE 'hn-%' THEN 1
            END ASC,
            created_at DESC
            """

    result={}

    for row in cur.execute(f"select id, post_id, category, title, post_url from {TABLE} where {query} order by {sort} limit {TAB_LIMIT}"):
        row=dict(row)
        id=row.pop("post_id")
        result[id]=row
    return jsonify(result)

# API endpoint to like/dislike a headline
@app.route('/api/headlines/<id>/<action>', methods=['GET'])
def action(id, action):

    category=(0 if action=="dislike" else 1)

    cur.execute(f"update {TABLE} set category={category}, sorted_at=coalesce( sorted_at, {int(datetime.datetime.today().astimezone(datetime.UTC).timestamp())}) where post_id={id}") # Only want to update sorted_at if it has not already been set
    
    for i in range(2):
        cur.execute(f"with deleted as (select * from {TABLE} where (sorted_at is not null) and (category={category}) order by sorted_at desc offset {HISTORY_LIMIT}) delete from deleted") #Keep only the most recently sorted

    return '', 200

cur_pool_lock=threading.Lock()
cur_pool=set()

def get_cur():
    cur=getattr(g, "cur", None)

    if cur is None:
        try:
            with cur_pool_lock:
                cur=cur_pool.pop()
        except KeyError:
            conn=sqlite3.connect(DATABASE, isolation_level=None)
            conn.row_factory = sqlite3.Row
            cur=conn.cursor()

        g.cur=cur
    return cur

cur=LocalProxy(get_cur)

@app.teardown_appcontext
def teardown_cur(dummy):
    cur=g.pop("cur")
    with cur_pool_lock:
        if len(cur_pool)<POOL_LIMIT:
            cur_pool.add(cur)
        else:
            cur.conn.close()


def update():
    result={}

    hn_stories=requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()
    
    ids={f"hn-{id}": id for id in hn_stories}

    query=f"""
    with ids (id) as (
    values {{placeholders}}
    )
    select ids.id
    from ids
    inner join {TABLE} t on ids.id=t.post_id;
    """
    
    #Check if ids are already in database, to filter out superfluous requests
    
    for id in cur.execute(query.format(placeholders=', '.join(['(?)'] * len(ids))), list(ids.keys())):
        del ids[id]
        
    
    with ThreadPoolExecutor(max_workers=10) as pool:
        while len(ids)>0:
            futures={pool.submit(lambda: requests.get(f"https://hacker-news.firebaseio.com/v0/item/{val}.json")):key for key, val in ids.items()}

            for future in as_completed(futures):
                response=future.result()
                if response.status_code==200:
                    data=response.json()

                    id=futures[future]
                    result[id]={"title": data["title"], "url": data.get("url", ""), "description": data.get("text", ""),  "tags": [],
                    "post_url": f"https://news.ycombinator.com/item?id={data['id']}", "created_at": data["time"]}

                    del ids[id]


    lobsters_stories=requests.get("https://lobste.rs/hottest.json").json()
    ids=[]
    for story in lobsters_stories:
        continue #Disable Lobste.rs integration for now --- hottest only returns the first page, when in fact, I want more than the first page

        id=f"lobsters-{story['short_id']}"
        ids.append(id)

        result[id]={"title": story["title"], "url": story["url"], "description": story["description_plain"], "tags": story["tags"],
        "post_url": story["short_id_url"], "created_at": int(datetime.datetime.fromisoformat(story["created_at"]).astimezone(datetime.UTC).timestamp())
        } 

    for id in cur.execute(query.format(placeholders=', '.join(['(?)'] * len(ids))), ids):
        del result[id]


    prompt="""
    * Instructions: Given below is a list of tuples --- for each tuple, the first part is the ID, while the second part is a dictionary of relevant information. These tuples need to be sorted into "Liked" and "Disliked" categories, based on the list of items in the "Previously Liked" and "Previously Disliked" categories, which are given below.

    * Expected Output Form: A JSON list of exactly two JSON sublists --- nothing more, nothing less. The first sublist should contain the ids of the tuples that are categorized in the "Liked" column, and the second sublist should contain the ids of the tuples that are categorized in the "Disliked" column. Every id in the list of tuples should either be categorized as "Liked" or "Disliked".

    * List of tuples: {tuples}

    * Previously Liked: {liked}

    * Previously Disliked: {disliked}
    """
    
    main_cols=["title", "url", "description", "tags"]

    select_query=f"select {' , '.join(main_cols)} in {TABLE} where category = ?"

    while len(result)>0:

        content=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent", params={"key": config["GEMINI_API_KEY"]}, json={"contents": 
        [
            {
                "parts":
                    [
                        {
                            "text": prompt.format(
                                            tuples=
                                                {id: {col: result[id][col] for col in main_cols} for id in result}.items(), liked=[dict(row) for row in cur.execute(select_query, 1)], disliked=[dict(row) for row in cur.execute(select_query, 0)])}]}]}).text

        print(content)

        liked, disliked=json.loads(content)

        inserted=[]
        
        for lst, category in [(liked, 1), (disliked, 0)]:
            for id in lst:
                row=result.get(id, None)
                if row:
                    row["post_id"]=id
                    row["category"]=category
                    inserted.append(row)
                    del result[id]
        if len(inserted)>0:
            cur.executemany(f"insert into {TABLE} values ({', '.join([':'+col for col in inserted[0].keys()])})", inserted)
        
       
if not os.environ.get("RELOEADER_HAS_RUN"): #Environment guard --- otherwise, the exit handlers will be set for both the reloader process and the actual application process, leading to files bein g overwritten twice.
    os.environ["RELOEADER_HAS_RUN"]="1"
else:   
    def update_loop():
        while True:
            with app.app_context():
                update()
            time.sleep(1*60*60)

    threading.Thread(target=update_loop).start()
        

