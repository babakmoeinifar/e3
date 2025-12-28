import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


def _make_redis_client(host: str, port: int):
    return redis.Redis(host=host, port=port, decode_responses=True)


redis_client = _make_redis_client(REDIS_HOST, REDIS_PORT)
try:
    redis_client.ping()
except Exception:
    # If the default host failed and it's the docker-style host name,
    # try localhost which is common for running Redis locally.
    if REDIS_HOST != "localhost":
        try:
            redis_client = _make_redis_client("localhost", REDIS_PORT)
            redis_client.ping()
        except Exception:
            # keep the original client; connection errors will surface
            # when used elsewhere and should be handled there.
            pass
