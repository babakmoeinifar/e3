import json
from app.session.redis_client import redis_client
from app.session.eitaa_client import EitaaClient
from app.session.pool import pool as session_pool
import requests
from app.ai.groq_client import ask_groq
from app.ai.prompts import HASHTAG_PROMPT


def discover_channels():
    # Instantiate the client lazily using a token selected from the
    # session pool so we can operate with multiple Eita tokens.
    # Try to get trends using available sessions. If a token fails with
    # an auth error, mark it failed and try the next one.
    trends = redis_client.get("eitaa:trends")
    if not trends:
        trends = None
        tried = set()
        # attempt up to number of configured sessions + 1 (env fallback)
        attempts = len(session_pool._sessions) if hasattr(session_pool, "_sessions") else 0
        attempts = max(attempts, 1)
        for _ in range(attempts):
            token = session_pool.get()
            if not token or token in tried:
                break
            tried.add(token)
            client = EitaaClient(token=token)
            try:
                trends = client.get_trends()
                session_pool.mark_success(token)
                break
            except requests.HTTPError as e:
                # mark token failed on authentication-type errors
                status = getattr(e.response, "status_code", None)
                if status in (401, 403):
                    session_pool.mark_failed(token)
                    continue
                # other HTTP errors: re-raise
                raise
        if trends is not None:
            redis_client.setex("eitaa:trends", 3600, json.dumps(trends))
        else:
            trends = []

     # 2️⃣ هشتگ‌ها (AI)
    hashtags = redis_client.get("eitaa:hashtags")
    if not hashtags:
        hashtags = ask_groq(
            HASHTAG_PROMPT.format(trends=trends)
        )
        redis_client.setex("eitaa:hashtags", 7200, json.dumps(hashtags))
    else:
        hashtags = json.loads(hashtags)

    # Normalise hashtags: ask_groq may return a JSON array string, or a
    # newline/comma-separated string. Ensure we have a list of tags.

    if isinstance(hashtags, str):
        try:
            parsed = json.loads(hashtags)
            if isinstance(parsed, list):
                hashtags = parsed
            else:
                # Not a list; fall through to splitting
                raise ValueError
        except Exception:
            # Split on newlines or commas as a best-effort fallback
            hashtags = [h.strip() for h in hashtags.replace("\n", ",").split(",") if h.strip()]

    # 3️⃣ کشف کانال
    channels = set()

    for tag in hashtags:
        # Attempt to fetch messages using available sessions; if a
        # session fails due to auth, mark it failed and try the next one.
        messages = None
        tried = set()
        attempts = len(session_pool._sessions) if hasattr(session_pool, "_sessions") else 0
        attempts = max(attempts, 1)
        for _ in range(attempts):
            token = session_pool.get()
            if not token or token in tried:
                break
            tried.add(token)
            client = EitaaClient(token=token)
            try:
                messages = client.search_messages(tag, limit=50)
                session_pool.mark_success(token)
                break
            except requests.HTTPError as e:
                status = getattr(e.response, "status_code", None)
                if status in (401, 403):
                    session_pool.mark_failed(token)
                    continue
                raise

        if not messages:
            continue

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            ch = msg.get("channel")
            if not ch:
                continue

            key = f"eitaa:channel:seen:{ch}"
            if redis_client.exists(key):
                continue

            redis_client.set(key, 1)
            channels.add(ch)

    return list(channels)
