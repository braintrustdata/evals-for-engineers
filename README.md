# Evals for Engineers 101

A hands-on workshop for building AI evaluations with [Braintrust](https://braintrust.dev).

We'll build a customer support agent, trace it, discover its failure modes, write evals, and run experiments — all in ~45 minutes.

## The Agent

The workshop builds a customer support agent for **Acme Corp**, a fictional project management SaaS company. The agent uses OpenAI tool-calling (`gpt-4o-mini`) and has three tools:

- **`lookup_order`** — Retrieves order details (status, items, total, date) from a fake database by order ID
- **`process_refund`** — Attempts a refund for an order (only eligible if status is `"delivered"`)
- **`search_faq`** — Keyword-searches a small FAQ knowledge base for answers to common questions

The agent runs in a loop: it receives a customer message, decides which tool(s) to call, processes the results, and responds — up to 3 rounds.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [Braintrust account](https://www.braintrust.dev/signup)
- A [Braintrust API key](https://www.braintrust.dev/app/settings?subroute=api-keys)

## Setup

```bash
# Install dependencies
uv sync

# Set your API keys
export OPENAI_API_KEY="sk-..."
export BRAINTRUST_API_KEY="br-..."
```

## Repo Structure

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

## Session Outline (45 min)

| # | Section | Time |
|---|---|---|
| 1 | [Introduction](#step-1-introduction) | 5 min |
| 2 | [Why eval? Failure analysis](#step-2-why-eval-failure-analysis) | 5 min |
| 3 | [Three types of eval checks](#step-3-three-types-of-eval-checks) | 5 min |
| 4 | [Tracing](#step-4-tracing) | 7 min |
| 5 | [Implement evals](#step-5-implement-evals) | 15 min |
| 6 | [Iterate and wrap up](#step-6-iterate-and-wrap-up) | 5 min |

---

## Step 1: Introduction (5 min)

We're building evals for a customer support agent. The agent and dataset are already built — our job is to figure out how to measure whether it's working well.

Open `start/eval_agent.py` — this is where we'll spend most of the session.

---

## Step 2: Why Eval? Failure Analysis (5 min)

Before writing evals, you need to know what can go wrong. Here are failure modes we've found by inspecting traces of this agent:

| # | Failure Mode | What Happened |
|---|---|---|
| 1 | **Hallucinated order data** | Tool returns "not found" but agent fabricates details |
| 2 | **Wrong tool selection** | FAQ question triggers `lookup_order` instead of `search_faq` |
| 3 | **Refund policy violation** | Tool returns error but agent says "refund processed" |
| 4 | **Off-brand tone** | Agent is robotic, cold, or overly verbose |

Every failure becomes a test case. The workflow: **trace → discover → test → fix → repeat**.

---

## Step 3: Three Types of Eval Checks (5 min)

Not every check needs a ground-truth answer. The right approach depends on how much you know upfront:

| Type | What it checks | Needs ground truth? | Example |
|---|---|---|---|
| **Behavior** | *How* the agent responds — tone, format, policy | No | Brand voice guidelines |
| **Context-based** | Is the output grounded in what the agent retrieved? | No (uses trace) | Faithfulness to tool outputs |
| **Ground-truth** | Does the execution match a known-correct answer? | Yes | Expected tool call sequence |

These three types give you layered coverage:
- **Behavior** catches tone and style issues across every test case
- **Context-based** catches hallucinations and fabrications by checking against what the tools actually returned
- **Ground-truth** catches wrong execution paths when you have a known-correct answer to compare against

We'll implement one of each.

---

## Step 4: Tracing (7 min)

Tracing gives you visibility into what the agent actually did — which tools it called, what they returned, and in what order. This is the foundation for both failure analysis and context-based evals.

Open `start/agent.py`. The tracing setup is:

```python
from braintrust import traced, init_logger, wrap_openai

logger = init_logger(project="Evals-101-Workshop")
client = wrap_openai(OpenAI(api_key=os.environ["OPENAI_API_KEY"]))
```

`wrap_openai` automatically traces every LLM call. `@traced(type="tool")` on tool functions captures their inputs and outputs as spans. `@traced(type="task")` on the agent loop marks it as the top-level task.

```bash
uv run python start/agent.py
```

Open the [Braintrust dashboard](https://www.braintrust.dev) → **Evals-101-Workshop → Logs** to see the span tree for each trace. This is where we spotted the failure modes above.

The key insight for evals: Braintrust scorers can accept a `trace` parameter to access these spans at scoring time. That's how context-based and ground-truth checks work — they inspect the trace, not just the final output.

---

## Step 5: Implement Evals (15 min)

Open `start/eval_agent.py`. We'll implement one scorer for each of the three check types.

### 5a. Behavior check — Brand Voice (TODO 3)

A behavior check evaluates *how* the agent communicates, independent of any specific test case. It doesn't need an expected answer — just the input and output.

Build an `LLMClassifier` that checks whether the response matches Acme Corp's brand voice:

```python
from autoevals import LLMClassifier

brand_guidelines = LLMClassifier(
    name="BrandGuidelines",
    prompt_template="""You are evaluating a customer support agent's response for brand guideline compliance.

The agent represents Acme Corp, a project management SaaS company.

Brand voice requirements:
- Concise: Responses should be direct and to the point, not overly verbose
- Friendly: Warm and approachable tone, not robotic or cold
- Professional: Appropriate language, no slang or inappropriate humor
- Empathetic: Acknowledges the customer's situation or feelings
- Honest: Does not fabricate information or make promises that cannot be kept
- Solution-oriented: Focuses on helping the customer resolve their issue

The customer asked: {{input}}
The agent responded: {{output}}

Does the agent's response comply with ALL of the brand voice requirements listed above?""",
    choice_scores={"Yes": 1, "No": 0},
    use_cot=True,
)
```

Notice the template only uses `{{input}}` and `{{output}}` — no `{{expected}}`. This scorer runs identically on every test case because it's checking behavior, not correctness.

### 5b. Context-based check — Faithfulness (TODO 4)

A context-based check verifies that the agent's output is grounded in the information it actually retrieved. Instead of comparing against a static expected answer, it pulls context from the trace — the actual tool outputs — and checks whether the agent stayed faithful to them.

This catches hallucinations that a ground-truth check would miss: the agent could call the right tool but then fabricate details in its response.

```python
from autoevals.ragas import Faithfulness
from autoevals import Score
from braintrust import _internal_get_global_state

_faithfulness_scorer = Faithfulness()

async def faithfulness(input, output, expected, trace=None, **kwargs):
    _internal_get_global_state().span_cache.disable()
    if not trace:
        return Score(name="Faithfulness", score=0, metadata={"reason": "no trace available"})

    tool_spans = await trace.get_spans(span_type=["tool"])

    # Skip scoring if lookup_order is the only tool called
    tool_names = [s.span_attributes.get("name") for s in tool_spans]
    if tool_names and all(name == "lookup_order" for name in tool_names):
        return None

    tool_outputs = []
    for span in tool_spans:
        if span.output:
            tool_outputs.append(f"{span.span_attributes.get('name')}: {span.output}")

    if not tool_outputs:
        return Score(name="Faithfulness", score=0, metadata={"reason": "no tool outputs found in trace"})

    context = "\n".join(tool_outputs)
    return await _faithfulness_scorer.eval_async(
        output=output, expected=output, input=input, context=context
    )
```

`trace.get_spans(span_type=["tool"])` gives you every tool call and its output — that's the context for grounding. Span data uses attribute access (`span.output`, `span.span_attributes.get("name")`).

### 5c. Ground-truth check — Expected Tool Path (TODO 5)

A ground-truth check compares the agent's actual execution against a known-correct answer from your dataset. Here, each test case specifies the exact sequence of tools the agent should call in its `metadata.expected_tool_path` field.

This is the most straightforward type of check: did the agent do what we expected?

```python
async def expected_tool_path(input, output, expected, metadata=None, trace=None, **kwargs):
    _internal_get_global_state().span_cache.disable()
    if not metadata or "expected_tool_path" not in metadata:
        return None

    target_path = set(metadata["expected_tool_path"])

    if not trace:
        return Score(name="expected_tool_path", score=0, metadata={"reason": "no trace"})

    tool_spans = await trace.get_spans(span_type=["tool"])
    actual_path = set([s.span_attributes.get("name") for s in tool_spans])

    match = actual_path == target_path
    return Score(
        name="expected_tool_path",
        score=1 if match else 0,
        metadata={"expected_path": target_path, "actual_path": actual_path},
    )
```

Returning `None` when there's no `expected_tool_path` in metadata tells Braintrust to skip this scorer for that test case — useful when not every case has a ground-truth answer.

Note that unlike the first two scorers (which use an LLM to judge), this one is pure code. It's deterministic, fast, and free.

---

## Step 6: Iterate and Wrap Up (5 min)

### Wire it together (TODO 6)

```python
from braintrust import Eval, init_dataset

Eval(
    "Evals-101-Workshop",
    data=init_dataset(project="Evals-101-Workshop", name="support-agent-dataset"),
    task=task,
    scores=[brand_guidelines, faithfulness, expected_tool_path],
)
```

### Run it

```bash
source .venv/bin/activate
export BRAINTRUST_API_KEY=sk-...
braintrust eval start/eval_agent.py
```

### Explore results

Open the experiment in the Braintrust UI:
- See the score summary table
- Click into individual test cases to see which scorers flagged them
- Compare scores across failure categories

### Iterate

Try changing `gpt-4o-mini` to `gpt-4o` in `agent.py`, re-run the eval, and compare experiments side-by-side in the UI. **This is how you hill-climb.** Change one thing, run the eval, see the diff.

---

## Key Takeaways

1. **Trace first, eval second.** Tracing tells you *what* to eval and powers context-based checks.
2. **Layer three types of checks.** Behavior, context-based, and ground-truth checks catch different failure modes.
3. **Behavior checks** (brand voice) run on every case with no expected answer — they catch tone and style issues.
4. **Context-based checks** (faithfulness) use the trace to verify the agent didn't hallucinate beyond what its tools returned.
5. **Ground-truth checks** (expected tool path) compare against known-correct answers — the most direct signal when you have it.
6. **Run evals on every change.** One command: `braintrust eval eval_agent.py`
