from dotenv import load_dotenv
import os

load_dotenv()
def _get_env_stripped(key: str) -> str | None:
    v = os.getenv(key)
    if v is None:
        return None
    return v.strip()


GOOGLE_API_KEY = _get_env_stripped("GOOGLE_API_KEY")
GROQ_API_KEY = _get_env_stripped("GROQ_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment; check .env and spelling")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment; check .env and spelling")