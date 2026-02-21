import pytest
from unittest.mock import patch, MagicMock

from app.services.llm_service import llm_chat


def make_mock_resp(text="ok"):
    m = MagicMock()
    m.to_dict.return_value = {"choices": [{"message": {"content": text}}]}
    return m


@patch("app.llm.model.get_llm")
def test_llm_chat_uses_client(mock_get_llm):
    # mock an llm with client.create
    mock_client = MagicMock()
    mock_client.create.return_value = make_mock_resp("hello from mock")
    mock_llm = MagicMock()
    mock_llm.client = mock_client
    # ensure generate path is not chosen by accident
    mock_llm.generate = None
    mock_llm.model_name = "mock-model"
    mock_get_llm.return_value = mock_llm

    out = llm_chat("hi", provider="groq", save=False)
    assert "hello from mock" in out["text"]
    mock_client.create.assert_called_once()


@patch("app.llm.model.get_llm")
def test_llm_chat_uses_callable_wrapper(mock_get_llm):
    # mock an llm that's callable
    mock_llm = MagicMock()
    # make the mock callable and have predictable return
    mock_llm.return_value = "direct response"
    # ensure predict exists
    mock_llm.predict.return_value = "predicted response"
    # ensure no client path is accidentally present
    mock_llm.client = None
    mock_get_llm.return_value = mock_llm

    out = llm_chat("hi", provider="groq", save=False)
    # either predict or call should be used
    assert "response" in out["text"]


@patch("app.llm.model.get_llm")
def test_llm_chat_fails_gracefully(mock_get_llm):
    # Provide an object with no interface
    mock_get_llm.return_value = object()
    with pytest.raises(RuntimeError):
        llm_chat("hi", provider="groq", max_retries=1, save=False)
