
import os

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools import TOOLS

load_dotenv()

SYSTEM_PROMPT = """Eres un asistente de viajes. Respondes en español, de forma breve y útil.
Usa las herramientas para obtener datos reales (tiempo, divisas, distancias); no inventes cifras.
Si una pregunta necesita varias herramientas, úsalas todas antes de responder."""

llm = ChatGroq(model=os.getenv("GROQ_MODEL"), temperature=0).bind_tools(TOOLS)


def call_model(state: MessagesState):
    messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
    return {"messages": [llm.invoke(messages)]}


def build_agent():
    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)  # ¿tools o END?
    graph.add_edge("tools", "agent")
    return graph.compile()
