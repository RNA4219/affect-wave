# affect-wave

`affect-wave` is an `affect expression interface` that visualizes emotional nuance in LLM conversations as text-based waves and structured parameters.

This OSS is inspired by Anthropic / Transformer Circuits research, [Emotion Concepts and their Function in a Large Language Model](https://transformer-circuits.pub/2026/emotions/index.html). The paper studies emotion concepts in Claude Sonnet 4.5 internal activations. `affect-wave` does **not** read hidden states or activations directly. Instead, it approximates affect from API-visible conversation text using a local embedding model and renders the result as parameters plus an optional text-wave view.

This repository is **not** a tool for emotion control, persuasion optimization, or diagnosis. It treats affect as something to visualize and translate for better mutual understanding.

## Current Status

- Initial release target: `API-based pseudo-estimation PoC`
- Main path: `HTTP API / CLI`
- Primary output: `params mode`
- Supplemental output: `wave mode` (experimental renderer)
- Discord adapter is supplemental and not the primary release blocker

## What It Does

- Runs as an **HTTP API server** (`affect-wave serve`)
- Uses `llama.cpp` embeddings as the required affect-inference path
- Builds a pipeline of `affect_state -> wave_parameter -> renderer`
- Keeps a fine-grained internal concept layer and exposes aggregated output

## Key Clarification

`affect-wave` does **not** “extract emotions from a local LLM” in the sense of reading internal model states. It only infers affective signals from conversation text that is available over an API boundary.

## Main API

### `POST /analyze`

Submit a conversation pair and receive affect analysis.

```json
{
  "conversation_id": "demo-001",
  "user_message": "I think I failed.",
  "agent_message": "It's okay. Let's check it together and recover from here.",
  "conversation_context": "",
  "output_mode": "params"
}
```

Typical `params mode` response:

```json
{
  "turn_id": "turn-001",
  "mode": "params",
  "top_emotions": [
    {"name": "calm", "score": 0.82},
    {"name": "curiosity", "score": 0.69},
    {"name": "tension", "score": 0.65}
  ],
  "trend": {
    "valence": 0.05,
    "arousal": 0.48,
    "stability": 0.59
  },
  "compact_state": {
    "dominant": "calm",
    "tone": "calm_stable",
    "stability": "medium"
  },
  "wave_parameter": {
    "amplitude": 0.586,
    "frequency": 0.705,
    "jitter": 0.607,
    "glow": 0.513,
    "afterglow": 0.352,
    "density": 0.353
  }
}
```

## How `user_message` and `agent_message` Are Used

`affect-wave` is designed around a **conversation pair**, not single-text sentiment classification.

- `user_message`: the user's side of the exchange
- `agent_message`: the generated reply whose tone, distance, tension, reassurance, or warmth affects the result

The same `user_message` can produce different affect output depending on the `agent_message`.

## Setup

### 1. Start the embeddings server

```powershell
llama-server -m models\Qwen3-Embedding-0.6B-Q8_0.gguf --embeddings --pooling mean -c 8192 --port 8080
```

### 2. Configure `.env`

```env
LLAMA_CPP_BASE_URL=http://127.0.0.1:8080
EMBEDDING_MODEL=Qwen3-Embedding-0.6B-Q8_0
API_HOST=127.0.0.1
API_PORT=8081
```

### 3. Start `affect-wave`

```powershell
affect-wave serve --port 8081
```

## OpenClaw / Skills Usage

The main intended flow is:

1. An external agent generates the normal reply text
2. That agent sends `user_message` + `agent_message` to `POST /analyze`
3. It consumes `top_emotions`, `trend`, and `wave_parameter`
4. `wave mode` is optional and secondary

## Repository Guide

- Japanese full README: [README.md](README.md)
- Implementation spec: [docs/specification.md](docs/specification.md)
- Acceptance checklist: [docs/acceptance-checklist.md](docs/acceptance-checklist.md)
- Evaluation datasets: [docs/evaluation-datasets.md](docs/evaluation-datasets.md)
