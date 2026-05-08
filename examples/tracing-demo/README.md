# Distributed Tracing Demo

This demo shows end-to-end OpenTelemetry distributed tracing across three services:

```
demo_agent.py
    └── POST /api/v1/llm/chat        (Vectaris LLM proxy)
            └── POST /v1/chat/completions   (mock OpenAI server)
```

Every hop creates an OTel span. Because the `traceparent` W3C header is propagated
through each request, all spans share the same **trace ID** and appear as a single
waterfall in any trace visualiser.

## Setup

```bash
pip install -r examples/tracing-demo/requirements.txt
```

## Run

Open three terminals:

**Terminal 1 — Mock OpenAI server** (simulates any OpenAI-compatible LLM):
```bash
python examples/tracing-demo/mock_openai_server.py
```

**Terminal 2 — Vectaris backend** (pointed at the mock):
```bash
cd backend
OPENAI_BASE_URL=http://localhost:9000 uvicorn app.main:app --port 8000 --reload
```

**Terminal 3 — Demo agent**:
```bash
python examples/tracing-demo/demo_agent.py
```

## With OTLP Export

To send traces to an OTLP collector (e.g. Jaeger, Tempo, or the Vectaris backend's
own OTLP ingress):

```bash
# In all three terminals, also set:
export OTEL_ENABLED=true
export VECTARIS_URL=http://localhost:8000
```

## Expected Output

```
[tracing-demo] Registered agent agent-abc123
[tracing-demo] Question 1/3
  Q: What is distributed tracing…
  A: Distributed tracing allows you to follow a request…
[tracing-demo] Question 2/3
  …
[tracing-demo] Done. Trace IDs printed above (Console) or sent to OTLP.
```

The Console exporter prints each span to stdout with its trace ID, span ID, parent
span ID, and duration — demonstrating the parent-child relationship across services.

## Ollama Variant

To use a local Ollama instance instead of the mock server:

```bash
# Start Ollama
ollama serve
ollama pull llama3

# Point Vectaris at Ollama
cd backend
OPENAI_BASE_URL=http://localhost:11434/v1 uvicorn app.main:app --port 8000 --reload

# Run the demo agent (no mock server needed)
python examples/tracing-demo/demo_agent.py
```

Ollama's OpenAI-compatible API means the demo works without any code changes.
The trace chain becomes: `demo_agent → Vectaris proxy → Ollama`.
