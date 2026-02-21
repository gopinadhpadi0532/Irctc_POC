from app.config import GOOGLE_API_KEY
from app.config import GROQ_API_KEY
import os


def get_llm(prefer_provider: str | None = None):
    """Return a LangChain chat model.

    Preference order:
    1. If `prefer_provider` is provided, try that provider ('google' or 'groq').
    2. Otherwise, use env `LLM_PROVIDER` (if set).
    3. Default to Google GenAI if credentials present, otherwise Groq.
    """
    provider = (prefer_provider or os.getenv("LLM_PROVIDER") or "google").lower()

    # Try Google Gemini via LangChain wrapper when requested
    if provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.3,
            )
        except Exception:
            # Fall through to Groq if Google wrapper isn't available or fails
            pass

    # Default / fallback: Groq
    try:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=GROQ_API_KEY,
            # Groq is very fast, but we'll keep retries just in case
            max_retries=3,
        )
    except Exception:
        raise RuntimeError("No supported LLM provider is installed (langchain_google_genai or langchain_groq required)")
