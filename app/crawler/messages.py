from app.session.eitaa_client import EitaaClient
from app.session.pool import pool as session_pool
from app.session.redis_client import redis_client
import requests


def fetch_messages(channel_username, limit=50):
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
            messages = client.get_channel_messages(channel_username, limit)
            session_pool.mark_success(token)
            break
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (401, 403):
                session_pool.mark_failed(token)
                continue
            raise

    if not messages:
        return []

    unique = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        msg_id = msg.get("id")
        if not msg_id:
            continue

        key = f"eitaa:msg:seen:{msg_id}"
        if redis_client.exists(key):
            continue

        redis_client.setex(key, 86400, 1)
        unique.append(msg)

    return unique
