import os
import requests

BASE_URL = "https://eitaayar.ir/api"


class EitaaClient:
    """Wrapper around eitaapykit (if installed) with a fallback to
    direct HTTP calls to the eitaayar.ir API. This keeps the public
    methods used by the rest of the code (`get_trends`,
    `search_messages`, `get_channel_messages`) unchanged while leveraging
    the higher-level `eitaa` package when available.
    """

    def __init__(self, token: str | None = None):
        # Allow passing a token explicitly (for multi-session support).
        # If not provided, fall back to the environment variable.
        if token:
            self._token = token
        else:
            # Read the token at instantiation time so environment variables
            # loaded earlier (for example via load_dotenv in main.py) are respected.
            self._token = os.getenv("EITAAYAR_TOKEN")

        if not self._token:
            raise RuntimeError("EITAAYAR_TOKEN تنظیم نشده است")

        # Try to use the eitaa toolkit if it's installed; otherwise we'll
        # fall back to direct HTTP requests to the eitaayar.ir API.
        try:
            from eitaa import Eitaa  # type: ignore
        except Exception:
            self._eitaa = None
        else:
            # Some methods on Eitaa are classmethods / static; also the
            # library allows instantiation with the token for instance
            # methods (e.g., send_message).
            self._eitaa = Eitaa
            try:
                # create an instance for instance methods if supported
                self._eitaa_instance = Eitaa(self._token)
            except Exception:
                self._eitaa_instance = None

        # Prepare headers for the HTTP fallback
        self._headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def get_trends(self):
        # Prefer using the eitaa package if available
        if getattr(self, "_eitaa", None):
            try:
                return self._eitaa.get_trends()
            except Exception:
                # Fall through to HTTP fallback on any unexpected error
                pass

        r = requests.get(
            f"{BASE_URL}/trends",
            headers=self._headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def search_messages(self, query, limit=50):
        # The eitaa toolkit doesn't document a generic search endpoint in
        # its README; keep the previous `/search` fallback as the
        # authoritative behavior. If the toolkit exposes a search
        # function in future, prefer it here.
        if getattr(self, "_eitaa", None):
            # try common names (non-breaking if not present)
            try:
                if hasattr(self._eitaa, "search"):
                    return self._eitaa.search(query, limit)
                if hasattr(self._eitaa_instance, "search"):
                    return self._eitaa_instance.search(query, limit)
            except Exception:
                pass

        r = requests.get(
            f"{BASE_URL}/search",
            params={"q": query, "limit": limit},
            headers=self._headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def get_channel_messages(self, username, limit=50):
        # Prefer `get_latest_messages` from the toolkit if present
        if getattr(self, "_eitaa", None):
            try:
                if hasattr(self._eitaa, "get_latest_messages"):
                    return self._eitaa.get_latest_messages(username)
                if hasattr(self._eitaa_instance, "get_latest_messages"):
                    return self._eitaa_instance.get_latest_messages(username)
            except Exception:
                pass

        r = requests.get(
            f"{BASE_URL}/channel/{username}/messages",
            params={"limit": limit},
            headers=self._headers,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
