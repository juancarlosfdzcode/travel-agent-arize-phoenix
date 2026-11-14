
"""Entry point: run the travel agent with Phoenix tracing enabled.

Usage:
    python main.py
    python main.py "Is it cold in Oslo? And how many Norwegian kroner is 200 euros?"
"""

import sys

from dotenv import load_dotenv
from phoenix.otel import register

load_dotenv()
register(auto_instrument=True)

from agent import build_agent

DEFAULT_QUESTION = (
    "I'm travelling from Madrid to Tokyo with 500 euros. "
    "How far is it, how many yen is that, and what's the weather there right now?"
)


def main() -> None:
    question = " ".join(sys.argv[1:]) or DEFAULT_QUESTION
    agent = build_agent()
    result = agent.invoke({"messages": [("user", question)]})

    for message in result["messages"]:
        message.pretty_print()


if __name__ == "__main__":
    main()
