from langgraph.graph import StateGraph, END
from app.graph.nodes import ChatState, planner_node, tool_node

def build_graph():
    workflow = StateGraph(ChatState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("tool_executor", tool_node)

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "tool_executor")
    workflow.add_edge("tool_executor", END)

    return workflow.compile()