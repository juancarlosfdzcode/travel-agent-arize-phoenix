import sys

from dotenv import load_dotenv
from phoenix.otel import register

load_dotenv()
register(auto_instrument=True)  # detecta LangChain/LangGraph y lo instrumenta solo

from agent import build_agent  # noqa: E402  (después de register, a propósito)

DEFAULT_QUESTION = (
    "Voy a viajar de Madrid a Tokio con 500 euros. "
    "¿Qué distancia hay, cuántos yenes son y qué tiempo hace allí ahora?"
)

question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION
agent = build_agent()
result = agent.invoke({"messages": [("user", question)]})

for message in result["messages"]:
    message.pretty_print()
