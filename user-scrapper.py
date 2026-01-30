import praw
import pandas as pd
from datetime import datetime


# ================= CONFIG =================

CLIENT_ID = "IQ7dyhpy9rye8HOCWdMDMg"
CLIENT_SECRET = "x2AJzeBP9qe1Sob81a92ZQYjyBDdxg"
USER_AGENT = "test_bot"


TARGET_USERNAME = "Reasonable_Cod_8762"   # Change this
POST_LIMIT = 300           # Max: ~1000 (API limit)
OUTPUT_FILE = "user_analytics.csv"


# ================= AUTH =================

def connect_reddit():
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
        check_for_async=False
    )


# ================= SCRAPER =================

def scrape_user(reddit):

    user = reddit.redditor(TARGET_USERNAME)

    data = []

    print(f"[INFO] Fetching posts for u/{TARGET_USERNAME}")

    for post in user.submissions.new(limit=POST_LIMIT):

        created = datetime.fromtimestamp(post.created_utc)

        engagement = post.score + post.num_comments

        record = {
            "post_id": post.id,
            "title": post.title,
            "subreddit": post.subreddit.display_name,
            "score_upvotes": post.score,
            "comments": post.num_comments,
            "engagement": engagement,
            "created_at": created.strftime("%Y-%m-%d %H:%M:%S"),
            "permalink": f"https://reddit.com{post.permalink}"
        }

        data.append(record)

    return data


# ================= SAVE =================

def save_csv(data):

    df = pd.DataFrame(data)

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"[SUCCESS] Saved {len(df)} posts → {OUTPUT_FILE}")


# ================= MAIN =================

def main():

    reddit = connect_reddit()

    data = scrape_user(reddit)

    save_csv(data)


if __name__ == "__main__":
    main()