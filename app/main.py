import sys
from pathlib import Path

# Ensure project root is on sys.path so `app` package imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from langchain_core.messages import HumanMessage
from app.graph.builder import build_graph

st.set_page_config(page_title="IRCTC AI Assistant")
st.title("🚆 IRCTC AI Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

graph = build_graph()

user_input = st.chat_input("Ask about trains, availability, policies...")

if user_input:
    st.session_state.messages.append(HumanMessage(content=user_input))
    result = graph.invoke({"messages": st.session_state.messages})
    st.session_state.messages = result["messages"]

for msg in st.session_state.messages:
    if msg.type == "human":
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("assistant").write(msg.content)