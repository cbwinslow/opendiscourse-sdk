"""
Ingest social media posts (Twitter/X, Mastodon, etc.) for tracked entities into the RAG database.
- Fetches posts, links to entities, and stores as declarations.
- Requires API credentials for each platform.
"""
import os

import psycopg2
import requests

DB_URL = os.environ.get("RAG_DB_URL", "postgresql://user:pass@localhost:5432/opendiscourse")

# Example: Twitter API v2 Bearer Token
TWITTER_BEARER = os.environ.get("TWITTER_BEARER_TOKEN")


def connect_db():
    return psycopg2.connect(DB_URL)

def fetch_twitter_posts(username, max_results=20):
    url = f"https://api.twitter.com/2/tweets/search/recent?query=from:{username}&max_results={max_results}"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("data", [])
    return []

def get_entity_id(cur, name):
    cur.execute("SELECT id FROM entities WHERE name=%s", (name,))
    row = cur.fetchone()
    return row[0] if row else None

def store_posts(entity_name, posts):
    conn = connect_db()
    cur = conn.cursor()
    entity_id = get_entity_id(cur, entity_name)
    if not entity_id:
        print(f"Entity not found: {entity_name}")
        return
    for post in posts:
        cur.execute(
            """
            INSERT INTO declarations (entity_id, text, date, type, source)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (entity_id, post['text'], post.get('created_at'), 'tweet', 'twitter')
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Stored {len(posts)} posts for {entity_name}")

def ingest_twitter(entity_name, username):
    posts = fetch_twitter_posts(username)
    store_posts(entity_name, posts)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python ingest_social_media.py <entity_name> <twitter_username>")
        exit(1)
    ingest_twitter(sys.argv[1], sys.argv[2])
