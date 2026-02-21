from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from app.llm.model import get_llm
from app.services.irctc_service import (
    search_trains,
    check_availability,
    cancellation_policy
)

# ---- Define State ----
class ChatState(TypedDict):
    messages: List[BaseMessage]
    action: str


# ---- Planner Node ----
def planner_node(state: ChatState):
    llm = get_llm()

    system_prompt = """
    You are an IRCTC assistant.

    Decide what action is needed based on the user's last message:
    - search_trains
    - check_availability
    - cancellation_policy
    - general_chat

    Respond ONLY with one of these action names.
    """

    response = llm.invoke(
        state["messages"] + [HumanMessage(content=system_prompt)]
    )

    action = response.content.strip()

    return {
        "messages": state["messages"],
        "action": action
    }


# ---- Tool Execution Node ----
def tool_node(state: ChatState):

    action = state["action"]

    if action == "search_trains":
        result = search_trains("Hyderabad", "Delhi")

    elif action == "check_availability":
        result = check_availability("12301")

    elif action == "cancellation_policy":
        result = cancellation_policy()

    else:
        # If general chat, just return state unchanged
        return state

    state["messages"].append(
        AIMessage(content=str(result))
    )

    return state