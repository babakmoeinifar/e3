import time
from app.session.redis_client import redis_client

def soft_rate_limit(key, interval=2):
    last = redis_client.get(key)
    now = time.time()

    if last:
        delta = now - float(last)
        if delta < interval:
            time.sleep(interval - delta)

    redis_client.set(key, now)
