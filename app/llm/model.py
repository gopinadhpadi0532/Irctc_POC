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
        # Development fallback: return a tiny local stub LLM so the app can run
        # without external provider packages/keys. This stub implements the
        # common methods the codebase calls (`predict`, `__call__`, and
        # `generate`) and returns simple action names based on the prompt.
        class _LocalDevLLM:
            def predict(self, prompt: str):
                p = (prompt or "").lower()
                if "cancel" in p or "cancellation" in p:
                    return "cancellation_policy"
                if "availability" in p or "available" in p or "check availability" in p:
                    return "check_availability"
                if "search" in p or ("from" in p and "to" in p) or "find trains" in p:
                    return "search_trains"
                # default to general chat for anything else
                return "general_chat"

            def __call__(self, prompt: str):
                return self.predict(prompt)

            def generate(self, messages):
                # messages may be a nested list in some wrappers; try to find text
                text = None
                try:
                    # handle list-of-lists [[HumanMessage]] or [[{"type":...,"content":...}]]
                    if isinstance(messages, list):
                        # dig into last message
                        last = messages[-1]
                        if isinstance(last, list):
                            last = last[-1]
                        # try attribute
                        text = getattr(last, "content", None)
                        if text is None and isinstance(last, dict):
                            text = last.get("content")
                except Exception:
                    text = None

                text = text or str(messages)
                action = self.predict(text)

                class _Gen:
                    def __init__(self, action_text):
                        self._action = action_text

                    def to_dict(self):
                        return {"choices": [{"message": {"content": self._action}}]}

                return _Gen(action)

        return _LocalDevLLM()
