import os
import groq
from groq import Groq

_client = None

def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not set. "
                "Set GROQ_API_KEY to use the Groq API."
            )
        _client = Groq(api_key=api_key)
    return _client

def ask_groq(prompt: str) -> dict:
    client = _get_client()
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Try the configured model, then fall back to a short list of
    # alternative models if Groq reports the model is decommissioned.
    tried_models = []
    fallback_models = [model, "llama3-13b-8192", "llama3-7b-4096", "llama3-3b-4096"]

    last_error = None
    for m in fallback_models:
        if m in tried_models:
            continue
        tried_models.append(m)
        try:
            response = client.chat.completions.create(
                model=m,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )
            # success
            return response.choices[0].message.content
        except groq.BadRequestError as e:
            last_error = e
            err_text = str(e)
            # If the error mentions decommissioned model, try next fallback
            if "decommissioned" in err_text or (hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 400):
                continue
            # For other BadRequest reasons, raise with context
            raise RuntimeError(
                f"Groq API returned a BadRequest error for model '{m}': {e}"
            ) from e

    # If we reach here, all fallback models failed.
    raise RuntimeError(
        "All attempted Groq models failed (tried: {}). Last error: {}".format(
            ",".join(tried_models), last_error
        )
    )
