import json
import time
import random
from pathlib import Path
from typing import List, Optional


class SessionPool:
    """Round-robin session pool with simple health tracking.

    Behavior:
    - Loads session JSON files from the sessions/ directory and extracts
      `auth_key` and optional `session_id` and `valid` fields.
    - Exposes a shared module-level `pool` instance (created below).
    - `get()` returns the next healthy token using round-robin. If no
      healthy sessions are available, returns the `EITAAYAR_TOKEN` env var.
    - `mark_failed(token)` updates failure counters and sets a backoff
      window; `mark_success(token)` resets its failure counters.
    """

    def __init__(self, sessions_dir: str = "sessions"):
        self.dir = Path(sessions_dir)
        self._load_sessions()
        self._index = 0

    def _load_sessions(self):
        self._sessions: List[dict] = []
        if not self.dir.exists():
            return
        for p in sorted(self.dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                key = data.get("auth_key")
                sid = data.get("session_id") or p.stem
                valid = data.get("valid", True)
                if key and valid:
                    self._sessions.append({
                        "token": key,
                        "id": sid,
                        "fail_count": 0,
                        "last_failed": 0.0,
                    })
            except Exception:
                # ignore malformed session files
                continue

    def _now(self) -> float:
        return time.time()

    def _backoff_seconds(self, fail_count: int) -> int:
        # exponential-ish backoff with min 30s, cap 1 hour
        return min(60 * (2 ** (fail_count - 1)) if fail_count > 0 else 0, 3600)

    def get(self) -> Optional[str]:
        """Return next healthy token or fallback to env var.

        This implements round-robin selection and skips tokens that are
        currently in backoff due to recent failures.
        """
        n = len(self._sessions)
        if n == 0:
            import os

            return os.getenv("EITAAYAR_TOKEN")

        # Try up to n sessions starting at current index
        for attempt in range(n):
            idx = (self._index + attempt) % n
            s = self._sessions[idx]
            # check backoff
            if s["fail_count"] > 0:
                backoff = self._backoff_seconds(s["fail_count"])
                if self._now() - s["last_failed"] < backoff:
                    continue
            # choose this session
            self._index = (idx + 1) % n
            return s["token"]

        # nothing healthy; fallback to env var
        import os

        return os.getenv("EITAAYAR_TOKEN")

    def mark_failed(self, token: str) -> None:
        for s in self._sessions:
            if s.get("token") == token:
                s["fail_count"] = s.get("fail_count", 0) + 1
                s["last_failed"] = self._now()
                return

    def mark_success(self, token: str) -> None:
        for s in self._sessions:
            if s.get("token") == token:
                s["fail_count"] = 0
                s["last_failed"] = 0.0
                return


# Shared pool instance used across the application so state (index,
# health) is preserved.
pool = SessionPool()

