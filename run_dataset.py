
"""Run every question in data/questions.json through the agent and trace it in Phoenix.

Each run is tagged with its question id and category, so you can filter traces in
Phoenix. A summary of which tools were called (vs. expected) is printed and saved
to results/.

Usage:
    python run_dataset.py              # all questions
    python run_dataset.py q04 q11      # only some questions
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from phoenix.otel import register

load_dotenv()
tracer_provider = register(auto_instrument=True)

from langchain_core.messages import AIMessage
from openinference.instrumentation import using_attributes

from agent import build_agent

DATASET_PATH = Path("data/questions.json")
RESULTS_DIR = Path("results")
PAUSE_SECONDS = 2  # stay under Groq's free-tier rate limits


def run_question(agent, item: dict) -> dict:
    """Run one question and return what the agent did."""
    started_at = time.perf_counter()
    with using_attributes(
        session_id=f"dataset-{item['id']}",
        tags=[item["category"]],
        metadata={"question_id": item["id"], "category": item["category"]},
    ):
        try:
            result = agent.invoke({"messages": [("user", item["question"])]})
        except Exception as error:
            return {**item, "status": "error", "error": repr(error),
                    "tools_called": [], "llm_calls": 0, "answer": None,
                    "seconds": round(time.perf_counter() - started_at, 2)}

    ai_messages = [m for m in result["messages"] if isinstance(m, AIMessage)]
    tools_called = [call["name"] for m in ai_messages for call in m.tool_calls]
    return {
        **item,
        "status": "ok",
        "tools_called": tools_called,
        "tools_match": sorted(tools_called) == sorted(item["expected_tools"]),
        "llm_calls": len(ai_messages),
        "answer": ai_messages[-1].content if ai_messages else None,
        "seconds": round(time.perf_counter() - started_at, 2),
    }


def print_summary(results: list[dict]) -> None:
    print(f"\n{'id':<5} {'category':<15} {'match':<6} {'llm':>3} {'secs':>6}  tools called")
    print("-" * 80)
    for r in results:
        match = "ERR" if r["status"] == "error" else ("yes" if r["tools_match"] else "no")
        print(f"{r['id']:<5} {r['category']:<15} {match:<6} {r['llm_calls']:>3} "
              f"{r['seconds']:>6}  {', '.join(r['tools_called']) or '-'}")
    matches = sum(1 for r in results if r.get("tools_match"))
    print("-" * 80)
    print(f"Expected tools matched: {matches}/{len(results)}")


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    selected_ids = set(sys.argv[1:])
    if selected_ids:
        dataset = [item for item in dataset if item["id"] in selected_ids]

    agent = build_agent()
    results = []
    for index, item in enumerate(dataset, start=1):
        print(f"[{index}/{len(dataset)}] {item['id']}: {item['question']}")
        results.append(run_question(agent, item))
        if index < len(dataset):
            time.sleep(PAUSE_SECONDS)

    print_summary(results)

    RESULTS_DIR.mkdir(exist_ok=True)
    output_path = RESULTS_DIR / f"run_{datetime.now():%Y%m%d_%H%M%S}.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Results saved to {output_path}")

    tracer_provider.force_flush()


if __name__ == "__main__":
    main()
