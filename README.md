# Travel Agent · Arize Phoenix

[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-green)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq-gpt--oss--120b-orange)](https://console.groq.com/)
[![Arize Phoenix](https://img.shields.io/badge/Arize%20Phoenix-Observability-purple)](https://github.com/Arize-ai/phoenix)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Tracing-lightgrey)](https://opentelemetry.io/)

A LangGraph travel assistant powered by Groq that checks the weather, converts currencies and calculates distances between cities — fully traced with [Arize Phoenix](https://github.com/Arize-ai/phoenix).

The goal of this project is to be a small, readable playground for **LLM agent observability**: every reasoning step, tool call, token count and latency is visible in Phoenix, so you can see exactly what the agent did and where it went wrong.

## How it works

The agent is a two-node LangGraph loop:

```
START → agent ──(tool calls?)── yes → tools ─┐
          ▲                                   │
          └───────────────────────────────────┘
                 no → END
```

- **`agent`** – the LLM (Groq, `openai/gpt-oss-120b` by default) reads the conversation and either answers or requests one or more tools.
- **`tools`** – runs the requested tools and sends the results back to the LLM.

The loop repeats until the LLM replies without requesting a tool.

### Tools

| Tool | What it does | Data source |
|---|---|---|
| `get_weather(city)` | Current temperature, sky condition and wind speed | [Open-Meteo](https://open-meteo.com/) (forecast + geocoding) |
| `convert_currency(amount, from_currency, to_currency)` | Converts between ISO currency codes | [Frankfurter](https://frankfurter.dev/) (ECB reference rates) |
| `get_distance(city_a, city_b)` | Great-circle distance in km | Open-Meteo geocoding + haversine formula |

All APIs are free and require **no API key**.

### Tracing

`main.py` calls `phoenix.otel.register(auto_instrument=True)`, which picks up the OpenInference LangChain instrumentor and exports OpenTelemetry spans to Phoenix. Each run shows up as a trace with nested spans for the graph, every LLM call (prompt, response, tokens) and every tool call (arguments and output).

## Project structure

```
travel-agent/
├── agent.py          # LangGraph graph (LLM node + tool node)
├── tools.py          # weather, currency and distance tools
├── main.py           # entry point with Phoenix tracing
├── check_groq.py     # smoke test: Groq API key and model
├── check_tools.py    # smoke test: tools without the LLM
├── run_dataset.py    # runs the question dataset, traced in Phoenix
├── data/
│   └── questions.json  # 15 test questions with expected tools
├── results/          # dataset run outputs (git-ignored)
├── requirements.txt
├── .env.example
└── README.md
```

## Getting started

### Prerequisites

- Python 3.10+
- A free [Groq API key](https://console.groq.com/keys)

### 1. Clone and install

```bash
git clone git@github.com:juancarlosfdzcode/travel-agent-arize-phoenix.git
cd travel-agent-arize-phoenix

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) | — |
| `GROQ_MODEL` | Groq model with tool-calling support | `openai/gpt-oss-120b` |
| `PHOENIX_COLLECTOR_ENDPOINT` | Where traces are sent | `http://localhost:6006` |
| `PHOENIX_PROJECT_NAME` | Project name in the Phoenix UI | `travel-agent` |

### 3. Start Phoenix

In a separate terminal (with the virtual environment activated):

```bash
phoenix serve
```

Open <http://localhost:6006>.

### 4. Run the smoke tests

```bash
python check_groq.py     # should print: Groq works
python check_tools.py    # should print three dictionaries
```

### 5. Run the agent

```bash
python main.py
```

Or ask your own question:

```bash
python main.py "Is it cold in Oslo? And how many Norwegian kroner is 200 euros?"
```

Then open the `travel-agent` project in Phoenix to inspect the trace.

### 6. Run the question dataset

`data/questions.json` holds 15 questions designed to exercise different behaviours. Each one has a category and the tools the agent is expected to call:

| Category | Questions | What it tests |
|---|---|---|
| `single_tool` | q01–q03 | One tool, one answer |
| `multi_tool` | q04–q06 | Several tools: called in parallel or one at a time? |
| `implicit_args` | q07 | Mapping "Mexican pesos" to `MXN` without help |
| `tool_limits` | q08 | Asking for tomorrow when the tool only has current weather |
| `no_tool` | q09 | General knowledge, no tool needed |
| `out_of_scope` | q10 | A request the agent cannot fulfil (booking a flight) |
| `error_handling` | q11, q13 | A fictional city and an unsupported currency |
| `ambiguity` | q12 | A city name shared by several places (Valencia) |
| `reasoning` | q14 | Combining a tool result with a calculation (travel time) |
| `language` | q15 | A question in Spanish when the prompt asks for English |

Run it with Phoenix running:

```bash
python run_dataset.py              # all questions
python run_dataset.py q04 q11      # only some questions
```

The script prints a summary table (expected tools matched, number of LLM calls, seconds, tools called) and saves the full results, including answers, to `results/run_<timestamp>.json`.

Every run is tagged in Phoenix with its category (`tag.tags`), question id (`metadata.question_id`) and a session id (`dataset-<question id>`), so you can filter traces by type or group all runs of the same question.

## What to look at in Phoenix

- **Span tree** – `LangGraph` → `agent` → `ChatGroq` → `tools` → `get_distance`… the graph loop, step by step.
- **LLM spans** – full prompt (including the system prompt), model response and token usage.
- **Tool spans** – the arguments the model chose and what each tool returned.
- **Latency** – how long each step takes. For example, whether the model calls independent tools one at a time (several LLM round trips) or in parallel.

## Troubleshooting

- **`model_not_found` from Groq** – Groq retires models regularly. Pick a current model with tool-use support from the [Groq models page](https://console.groq.com/docs/models) (see also [deprecations](https://console.groq.com/docs/deprecations)) and update `GROQ_MODEL` in `.env`.
- **No traces in Phoenix** – make sure `phoenix serve` is running, `PHOENIX_COLLECTOR_ENDPOINT` points to it, and `register()` is called *before* importing `agent`.
- **`City not found`** – the geocoder could not resolve the city name; try the English name or add the country (e.g. `"Valencia, Spain"`).


