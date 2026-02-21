from typing import Any, Dict, Optional
import time
import json
from datetime import datetime

# Import get_llm lazily inside the function so tests can patch app.llm.model.get_llm


def _extract_text_from_response(data: Any) -> str:
    """Try to extract a human-readable text from common response shapes."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        choices = data.get("choices")
        if choices and isinstance(choices, list) and len(choices) > 0:
            first = choices[0]
            # common shapes: {choices:[{message:{content: <str>}}]} or choices[0]['text']
            msg = first.get("message") if isinstance(first, dict) else None
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str):
                    return content
                # sometimes content is nested
                if isinstance(content, dict):
                    # try common nested text key
                    for k in ("text", "output_text", "content"):  # best-effort
                        v = content.get(k)
                        if isinstance(v, str):
                            return v
                    return json.dumps(content)
            # fallback to choices[0].get('text')
            if isinstance(first, dict) and isinstance(first.get("text"), str):
                return first.get("text")
        # last resort: stringify
        try:
            return json.dumps(data)
        except Exception:
            return str(data)
    # other types
    return str(data)


def llm_chat(prompt: str, provider: str = "groq", max_retries: int = 3, save: bool = True) -> Dict[str, Any]:
    """Send `prompt` to the project's preferred LLM and return a parsed response.

    Preference order for calling:
    1. If `llm` exposes `generate` (LangChain ChatModel), call it with a message-list.
    2. If `llm` is callable and accepts a string, call it directly.
    3. If `llm` exposes `client.create`, call the underlying client with a role/content payload.
    """
    from app.llm.model import get_llm
    llm = get_llm(prefer_provider=provider)
    last_err: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            data = None

            # Prefer provider-specific fast paths
            if provider == "groq" and hasattr(llm, "client") and hasattr(llm.client, "create"):
                # Try the common simple payload first (role + content string)
                payload1 = [{"role": "user", "content": prompt}]
                try:
                    resp = llm.client.create(model=getattr(llm, "model_name", getattr(llm, "model", None)), messages=payload1)
                    data = resp.to_dict() if hasattr(resp, "to_dict") else resp
                except Exception as e1:
                    # Some Groq endpoints accept content as a list of typed parts
                    payload2 = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
                    try:
                        resp = llm.client.create(model=getattr(llm, "model_name", getattr(llm, "model", None)), messages=payload2)
                        data = resp.to_dict() if hasattr(resp, "to_dict") else resp
                    except Exception as e2:
                        # Re-raise with both error contexts for easier debugging
                        raise RuntimeError(f"Groq client.create failed (tried two payload shapes). errors: {e1} | {e2}")

            # 1) If the wrapper is directly callable, try that first (predict or __call__)
            if data is None and callable(llm):
                try:
                    if hasattr(llm, "predict"):
                        data = llm.predict(prompt)
                    else:
                        data = llm(prompt)
                except Exception:
                    data = None

            # 2) LangChain-style generate (preferred for google)
            if data is None and hasattr(llm, "generate"):
                # try messages as list of lists [[HumanMessage]] if langchain is available
                try:
                    from langchain.schema import HumanMessage

                    messages = [[HumanMessage(content=prompt)]]
                    gen = llm.generate(messages)
                    # langchain generate returns a rich object; try to convert
                    data = gen.to_dict() if hasattr(gen, "to_dict") else gen
                except Exception:
                    # try a simpler call
                    try:
                        gen = llm.generate([[{"type": "human", "content": prompt}]])
                        data = gen.to_dict() if hasattr(gen, "to_dict") else gen
                    except Exception:
                        data = None

            # 2) Direct wrapper callable with string input
            if data is None and callable(llm):
                try:
                    if hasattr(llm, "predict"):
                        data = llm.predict(prompt)
                    else:
                        data = llm(prompt)
                except Exception:
                    data = None

            # 3) Underlying client
            if data is None and hasattr(llm, "client") and hasattr(llm.client, "create"):
                payload = [{"role": "user", "content": prompt}]
                resp = llm.client.create(model=getattr(llm, "model_name", getattr(llm, "model", None)), messages=payload)
                data = resp.to_dict() if hasattr(resp, "to_dict") else resp

            if data is None:
                raise RuntimeError("Unable to call LLM: no compatible interface found")

            # extract text
            text = _extract_text_from_response(data)

            # Optionally save a transcript
            if save:
                ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                path = f"./llm_transcript_{ts}.json"
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"prompt": prompt, "response": data}, f, ensure_ascii=False, indent=2)

            return {"text": text, "raw": data}

        except Exception as e:
            last_err = e
            backoff = 2 ** attempt
            time.sleep(backoff)

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_err}")
