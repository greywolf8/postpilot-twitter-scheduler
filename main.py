import os
import uuid
import base64
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from dotenv import load_dotenv
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore

from apscheduler.schedulers.background import BackgroundScheduler


# ------------------ ENV ------------------

load_dotenv()

CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

REDIRECT_URI = "http://localhost:8000/auth/twitter/callback"

SCOPES = "tweet.read tweet.write users.read offline.access"


# ------------------ FIREBASE ------------------

# Initialize Firebase only if it hasn't been initialized yet
if not firebase_admin._apps:
    cred = credentials.Certificate("postpilot-site-firebase-adminsdk-fbsvc-fe7f592c76.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ------------------ APP ------------------

app = FastAPI()


# ------------------ SCHEDULER ------------------

scheduler = BackgroundScheduler()
scheduler.start()


# ------------------ HELPERS ------------------

def find_user_by_email(email: str):

    users = db.collection("users") \
              .where("email", "==", email) \
              .limit(1) \
              .stream()

    for user in users:
        return user.id

    return None


def build_oauth_url(state: str):

    return (
        "https://twitter.com/i/oauth2/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&state={state}"
        f"&code_challenge=challenge"
        f"&code_challenge_method=plain"
    )


# ------------------ LOGIN ------------------

@app.get("/auth/twitter/login")
async def twitter_login(email: str):
    """
    Step 1:
    User provides email
    Backend finds user
    Starts OAuth
    """

    user_id = find_user_by_email(email)

    if not user_id:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    state = str(uuid.uuid4())

    # Save mapping
    db.collection("auth_states") \
      .document(state) \
      .set({
          "userId": user_id,
          "email": email,
          "createdAt": datetime.utcnow()
      })

    url = build_oauth_url(state)

    return RedirectResponse(url)


# ------------------ CALLBACK ------------------

@app.get("/auth/twitter/callback")
async def twitter_callback(code: str, state: str):
    """
    Step 2:
    Twitter redirects here
    We exchange tokens
    Save to Firestore
    """

    # Verify state
    state_doc = db.collection("auth_states") \
                  .document(state) \
                  .get()

    if not state_doc.exists:
        raise HTTPException(400, "Invalid OAuth state")

    user_id = state_doc.to_dict()["userId"]

    # Exchange code
    token_url = "https://api.twitter.com/2/oauth2/token"

    auth = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": "challenge"
    }

    async with httpx.AsyncClient() as client:

        res = await client.post(
            token_url,
            headers=headers,
            data=data
        )

        tokens = res.json()

    if "access_token" not in tokens:
        raise HTTPException(400, "Token exchange failed")


    expires_at = datetime.utcnow() + timedelta(
        seconds=tokens["expires_in"]
    )


    # Save Integration
    db.collection("users") \
      .document(user_id) \
      .collection("integrations") \
      .document("twitter") \
      .set({

          "accessToken": tokens["access_token"],
          "refreshToken": tokens.get("refresh_token"),
          "expiresAt": expires_at,

          "status": "active",
          "connectedAt": datetime.utcnow()

      })


    # Cleanup
    db.collection("auth_states") \
      .document(state) \
      .delete()


    return RedirectResponse(
        "http://localhost:3000/dashboard?twitter=connected"
    )


# ------------------ POST TWEET ------------------

async def post_tweet(token: str, text: str):

    url = "https://api.twitter.com/2/tweets"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:

        await client.post(
            url,
            headers=headers,
            json={"text": text}
        )


# ------------------ SCHEDULER ------------------

def scheduler_job():

    now = datetime.utcnow()

    users = db.collection("users").stream()

    for user in users:

        uid = user.id

        twitter = db.collection("users") \
                    .document(uid) \
                    .collection("integrations") \
                    .document("twitter") \
                    .get()

        if not twitter.exists:
            continue

        token = twitter.to_dict()["accessToken"]


        drafts = db.collection("users") \
            .document(uid) \
            .collection("drafts") \
            .where("platform", "==", "twitter") \
            .where("status", "==", "scheduled") \
            .where("scheduledAt", "<=", now) \
            .stream()


        for post in drafts:

            data = post.to_dict()

            try:

                import asyncio
                asyncio.run(
                    post_tweet(token, data["content"])
                )

                post.reference.update({
                    "status": "posted",
                    "postedAt": datetime.utcnow()
                })

            except Exception as e:

                post.reference.update({
                    "status": "failed",
                    "error": str(e)
                })


# Run every minute
scheduler.add_job(
    scheduler_job,
    "interval",
    minutes=1
)


# ------------------ RUN ------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )