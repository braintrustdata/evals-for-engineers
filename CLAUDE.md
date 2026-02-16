# Evals for Engineers 101

This is an **educational repo** for a hands-on workshop teaching tracing and evals using [Braintrust](https://www.braintrust.dev).

## What this repo teaches

Participants build a customer support agent (using OpenAI tool-calling), then learn to:

1. Add Braintrust tracing to get visibility into LLM calls and tool invocations
2. Discover failure modes by inspecting traces
3. Write heuristic and LLM-as-a-judge scorers
4. Run experiments with `braintrust` and `autoevals`

## Repo structure

The repo follows a **"cooking show"** format with two parallel sets of files:

- **`start/`** — Challenge files with TODOs and skeleton code. Braintrust is **not** implemented here. Participants work in this directory during the workshop.
- **`solution/`** — Complete answer key with Braintrust tracing, tool implementations, and eval scorers fully wired up.
- **`data.py`** — Shared module with fake order data, FAQs, tool schemas, and system prompt. Both `start/` and `solution/` import from it.

## Key conventions

- Python project managed with `uv` (see `pyproject.toml`)
- Uses OpenAI (`gpt-4o-mini`) for the agent LLM
- Uses `braintrust`, `autoevals`, and `openai` as core dependencies
- Braintrust project name: `Evals-101-Workshop`
- Evals are run via: `bt eval <path-to-eval-file>`

## When making changes

- Keep `start/` files free of Braintrust imports and implementations — they should only have TODOs and hints
- Keep `solution/` files as the complete working reference
- Both directories must stay in sync structurally (same filenames, same tool schemas, same data imports)
- `data.py` is shared — changes there affect both `start/` and `solution/`
