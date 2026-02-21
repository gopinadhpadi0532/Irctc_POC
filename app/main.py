import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from app.graph.builder import build_graph
from uuid import uuid4
from datetime import datetime

st.set_page_config(page_title="IRCTC AI Assistant")
st.title("🚆 IRCTC AI Assistant")

# --- Session state bootstrap ---
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid4())

if "messages" not in st.session_state:
    # store structured messages with metadata and an llm-compatible message object
    st.session_state.messages = []

graph = build_graph()


def _append_human_message(text: str):
    trace = str(uuid4())
    ts = datetime.utcnow().isoformat() + "Z"
    lm = HumanMessage(content=text)
    st.session_state.messages.append({
        "role": "human",
        "content": text,
        "trace_id": trace,
        "conversation_id": st.session_state.conversation_id,
        "timestamp": ts,
        "llm_msg": lm,
    })


def _sync_from_llm_messages(llm_messages):
    """Convert a list of BaseMessage objects from the graph back into
    our session message dicts (preserving existing metadata when possible)."""
    out = []
    for m in llm_messages:
        role = "human" if getattr(m, "type", None) == "human" or m.__class__.__name__ == "HumanMessage" else "assistant"
        content = getattr(m, "content", str(m))
        trace = str(uuid4())
        ts = datetime.utcnow().isoformat() + "Z"
        out.append({
            "role": role,
            "content": content,
            "trace_id": trace,
            "conversation_id": st.session_state.conversation_id,
            "timestamp": ts,
            "llm_msg": m,
        })
    st.session_state.messages = out


# --- Sidebar: conversation controls & quick actions ---
with st.sidebar:
    st.header("Conversation")
    st.write("Conversation ID:", st.session_state.conversation_id)
    if st.button("Start New Conversation"):
        st.session_state.conversation_id = str(uuid4())
        st.session_state.messages = []

    st.markdown("---")
    st.header("Quick Actions")
    quick = st.selectbox("Choose an action", ["", "Search Trains", "Check Availability", "Cancellation Policy", "Where is my train"], index=0)
    if quick:
        if st.button("Apply Quick Action"):
            if quick == "Search Trains":
                _append_human_message("Search trains from Hyderabad to Delhi")
            elif quick == "Check Availability":
                _append_human_message("Check availability for train 12301")
            elif quick == "Cancellation Policy":
                _append_human_message("Show cancellation policy")
            elif quick == "Where is my train":
                _append_human_message("Where is train 12301 now?")


# --- Main chat input handling ---
user_input = st.chat_input("Ask about trains, availability, policies...")

if user_input:
    _append_human_message(user_input)

    # Invoke the graph with the llm-ready messages
    llm_messages = [m["llm_msg"] for m in st.session_state.messages]
    result = graph.invoke({"messages": llm_messages})

    # result is expected to be a state dict; try to find returned messages
    if isinstance(result, dict) and "messages" in result:
        _sync_from_llm_messages(result["messages"])


# --- Render chat messages with metadata ---
for m in st.session_state.messages:
    if m["role"] == "human":
        with st.chat_message("user"):
            st.write(m["content"])
            with st.expander("Details"):
                st.write("Trace ID:", m["trace_id"])
                st.write("Conversation ID:", m["conversation_id"])
                st.write("Timestamp:", m["timestamp"])
    else:
        with st.chat_message("assistant"):
            st.write(m["content"])
            with st.expander("Details"):
                st.write("Trace ID:", m["trace_id"])
                st.write("Conversation ID:", m["conversation_id"])
                st.write("Timestamp:", m["timestamp"])