
"""LangGraph travel agent: an LLM node and a tool node running in a loop."""

import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools import TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are a travel assistant. Answer in English, briefly and helpfully.
Use the tools to get real data (weather, currency, distances); never make up numbers.
If a question needs several tools, use all of them before answering."""

llm_with_tools = ChatGroq(model=os.getenv("GROQ_MODEL"), temperature=0).bind_tools(TOOLS)


def call_model(state: MessagesState) -> dict:
    """Send the conversation to the LLM and append its reply (answer or tool calls)."""
    messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}


def build_agent():
    """Build and compile the graph: START -> agent -> (tools -> agent)* -> END."""
    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)  # route to "tools" or END
    graph.add_edge("tools", "agent")
    return graph.compile()
