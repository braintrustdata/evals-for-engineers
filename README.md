# Evals for Engineers 101

A hands-on workshop for building AI evaluations with [Braintrust](https://braintrust.dev).

We'll build a customer support agent, trace it, discover its failure modes, write evals, and run experiments — all in ~55 minutes.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [bt](https://github.com/braintrustdata/bt) (Braintrust CLI)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Braintrust API key](https://www.braintrust.dev/app/settings?subroute=api-keys)

## Setup

```bash
# Install bt CLI (if you haven't already)
curl -fsSL https://github.com/braintrustdata/bt/releases/latest/download/bt-installer.sh | sh

# Install dependencies
uv sync

# Set your API keys
export OPENAI_API_KEY="sk-..."
export BRAINTRUST_API_KEY="br-..."

# Log in to Braintrust
bt login
```

## Workshop Structure

This is a **"cooking show"** workshop. The `start/` directory has skeleton code with TODOs for live coding. The `solution/` directory has the complete answer key.

```
data.py          ← Shared data: orders, FAQs, tool schemas, system prompt

start/           ← Work here during the workshop
  agent.py       ← Agent skeleton with TODOs
  eval_agent.py  ← Eval skeleton with TODOs

solution/        ← Answer key (no peeking!)
  agent.py       ← Complete agent
  eval_agent.py  ← Complete eval suite
```

`data.py` is already done — it contains the fake order database and FAQ entries. Both `start/` and `solution/` import from it so you can focus on the agent logic and evals.

---

## Step 1: Build and Trace the Agent (15 min)

Open `start/agent.py`. The data and tool schemas are provided. You need to:

### 1a. Add Braintrust tracing (TODOs 1–3)

```python
from braintrust import traced, init_logger, wrap_openai, current_span

logger = init_logger(project="Evals-101-Workshop")
client = wrap_openai(OpenAI())
```

Two lines of code give you full visibility into every LLM call and tool invocation.

### 1b. Implement the tools (TODOs 4–7)

Add `@traced` to each tool function and implement:
- `lookup_order` — look up order in the `ORDERS` dict, return JSON or "not found"
- `process_refund` — check eligibility (only `"delivered"` orders), return result
- `search_faq` — keyword match against `FAQS` list

### 1c. Implement the agent loop (TODOs 8–9)

Add `@traced` to `support_agent` and implement the agentic loop:
1. Call `client.chat.completions.create()` with `model`, `messages`, and `tools`
2. If `finish_reason == "stop"` → return the content
3. Otherwise, process each `tool_call` and loop (up to 3 rounds)

### 1d. Generate traces

```bash
uv run python start/agent.py
```

Open the [Braintrust dashboard](https://www.braintrust.dev) and navigate to **Evals-101-Workshop → Logs** to see your traces.

---

## Step 2: Discover Failure Modes via Traces (10 min)

Look at the traces in the Braintrust UI. Expand each trace to see the span tree. You should find **4 failure modes**:

| # | Failure Mode | What to Look For |
|---|---|---|
| 1 | **Hallucinated order data** | Tool returns "not found" but agent fabricates details |
| 2 | **Wrong tool selection** | FAQ question triggers `lookup_order` instead of `search_faq` |
| 3 | **Refund policy violation** | Tool returns error but agent says "refund processed" |
| 4 | **FAQ mismatch** | Keyword matching returns irrelevant FAQ entry |

Every failure you find becomes a test case. That's the workflow: **trace → discover → test → fix → repeat**.

You can also use `bt` to browse traces interactively in your terminal:

```bash
bt -p "Evals-101-Workshop" traces
```

This opens an interactive trace viewer — use arrow keys to navigate, Enter to expand a trace, and `/` to search/filter. It's a fast way to spot patterns without leaving your terminal.

---

## Step 3: Code-Based Scorers (10 min)

Open `start/eval_agent.py`. First, add more test cases to cover each failure mode (TODO 2). Then build three heuristic scorers:

### Scorer 1: `keyword_match` (TODO 3)

Check if key phrases from the expected answer appear in the output.

```python
from autoevals import Score

def keyword_match(input, output, expected, **kwargs):
    keywords = [w.lower() for w in expected.split() if len(w) >= 4]
    matches = sum(1 for kw in keywords if kw in output.lower())
    return Score(name="keyword_match", score=matches / len(keywords))
```

### Scorer 2: `correct_tool_used` (TODO 4) — trace-based

Instead of guessing from output text, inspect the actual trace spans to see which tools were called. Braintrust scorers can accept a `trace` parameter to access the full execution trace.

```python
async def correct_tool_used(input, output, expected, metadata=None, trace=None, **kwargs):
    if not metadata or "expected_tool" not in metadata:
        return None

    all_spans = await trace.get_spans()
    tool_names_called = [s.get("name") for s in all_spans
        if s.get("name") in ("lookup_order", "process_refund", "search_faq")]

    used = metadata["expected_tool"] in tool_names_called
    return Score(name="correct_tool_used", score=1 if used else 0,
                 metadata={"expected": metadata["expected_tool"], "actual_tools": tool_names_called})
```

### Scorer 3: `no_hallucination_on_missing_order` (TODO 5) — trace-based

For `order_not_found` cases, verify via the trace that `lookup_order` returned "not found" AND that the agent's final output doesn't fabricate order details. Return `None` for other categories to skip.

```python
async def no_hallucination_on_missing_order(input, output, expected, metadata=None, trace=None, **kwargs):
    if not metadata or metadata.get("category") != "order_not_found":
        return None
    # Check output for hallucination + verify tool span returned "not found"
```

These scorers are **deterministic, fast, and free** — and trace-based scorers give you ground truth about what actually happened, not just what the output looks like.

---

## Step 4: LLM-as-a-Judge Scorers (10 min)

### Scorer 4: `Factuality` (TODO 6)

One import. Zero configuration. Compares output against expected answer.

```python
from autoevals import Factuality
# Just add Factuality to the scores list — it works out of the box
```

### Scorer 5: `PolicyCompliance` (TODO 7)

Build a custom `LLMClassifier` that checks refund policy compliance:

```python
from autoevals import LLMClassifier

policy_compliance = LLMClassifier(
    name="PolicyCompliance",
    prompt_template="""You are auditing a customer support agent's response...
The customer asked: {{input}}
The agent responded: {{output}}
The correct answer is: {{expected}}
Is the agent's response policy-compliant?""",
    choice_scores={"Yes": 1, "No": 0},
    use_cot=True,
)
```

### Scorer 6: `ClosedQA` (TODO 8)

Use `ClosedQA` with a custom criteria string for general answer quality:

```python
from autoevals import ClosedQA

answer_quality = ClosedQA(
    criteria="Is the response helpful, accurate, and does it address the customer's specific question?"
)
```

LLM-as-a-judge scorers fill the gap between simple heuristics and human review. **Combine both types for maximum coverage.**

---

## Step 5: Run Experiments (10 min)

### 5a. Wire it together (TODO 9)

```python
from braintrust import Eval

Eval(
    "Evals-101-Workshop",
    data=lambda: DATASET,
    task=lambda input: support_agent(input),
    scores=[keyword_match, correct_tool_used, no_hallucination_on_missing_order,
            Factuality, policy_compliance, answer_quality],
)
```

### 5b. Run it

```bash
bt eval start/eval_agent.py
```

### 5c. Explore results

Open the experiment in the Braintrust UI:
- See the score summary table
- Click into individual test cases to see which scorers flagged them
- Compare scores across failure categories

You can also browse experiment traces in your terminal:

```bash
bt -p "Evals-101-Workshop" traces
```

### 5d. Iterate (bonus)

Try changing `gpt-4o-mini` to `gpt-4o` in `agent.py`, re-run the eval, and compare experiments side-by-side in the UI:

```bash
bt eval start/eval_agent.py
```

**This is how you hill-climb.** Change one thing, run the eval, see the diff.

---

## Key Takeaways

1. **Trace first, eval second.** Tracing tells you *what* to eval.
2. **Start with heuristic scorers.** They're fast, free, and deterministic.
3. **Add LLM-as-a-judge for nuance.** `Factuality` and `ClosedQA` cover a lot out of the box.
4. **Build custom LLM judges for domain-specific policies.**
5. **Run evals on every change.** One command: `bt eval eval_agent.py`

The best eval is the one you actually run. Start simple, iterate fast.
