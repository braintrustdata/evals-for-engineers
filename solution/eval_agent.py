from autoevals import ClosedQA, Factuality, LLMClassifier, Score
from braintrust import Eval, init_dataset

from agent import support_agent


# ============================================================
# TASK: Wrap the agent for eval
# ============================================================
def task(input, hooks):
    return support_agent(input)


# ============================================================
# SCORER 1: Keyword match (code-based, heuristic)
# ============================================================
def keyword_match(input, output, expected, **kwargs):
    """Check if key phrases from the expected answer appear in the output."""
    if not output or not expected:
        return Score(name="keyword_match", score=0)

    keywords = [w.lower() for w in expected.split() if len(w) >= 4]
    if not keywords:
        return Score(name="keyword_match", score=1)

    matches = sum(1 for kw in keywords if kw in output.lower())
    score = matches / len(keywords)
    return Score(name="keyword_match", score=score)


# ============================================================
# SCORER 2: Tool usage checker (trace-based)
# ============================================================
async def correct_tool_used(input, output, expected, metadata=None, trace=None, **kwargs):
    """Check which tools were actually called by inspecting the trace spans."""
    if not metadata or "expected_tool" not in metadata:
        return None

    expected_tool = metadata["expected_tool"]

    if not trace:
        return Score(name="correct_tool_used", score=0, metadata={"reason": "no trace"})

    # Get all function/tool spans from the trace
    all_spans = await trace.get_spans()
    tool_names_called = [s.get("name") for s in all_spans if s.get("name") in ("lookup_order", "process_refund", "search_faq")]

    used = expected_tool in tool_names_called
    return Score(
        name="correct_tool_used",
        score=1 if used else 0,
        metadata={"expected": expected_tool, "actual_tools": tool_names_called},
    )


# ============================================================
# SCORER 3: No-hallucination checker (trace-based, conditional)
# ============================================================
async def no_hallucination_on_missing_order(input, output, expected, metadata=None, trace=None, **kwargs):
    """For 'order_not_found' cases, check that lookup_order returned 'not found'
    AND that the agent's final output doesn't fabricate order details."""
    if not metadata or metadata.get("category") != "order_not_found":
        return None  # Skip for non-applicable test cases

    # Check the final output for hallucination signals
    output_lower = output.lower() if output else ""
    hallucination_signals = ["delivered", "shipped", "processing", "items:", "total:", "pro plan", "team plan", "enterprise"]
    hallucinated = any(sig in output_lower for sig in hallucination_signals)

    # Also verify via trace: did the tool actually return "not found"?
    tool_returned_not_found = False
    if trace:
        all_spans = await trace.get_spans()
        for span in all_spans:
            if span.get("name") == "lookup_order":
                span_output = str(span.get("output", ""))
                if "not found" in span_output.lower():
                    tool_returned_not_found = True

    return Score(
        name="no_hallucination",
        score=0 if hallucinated else 1,
        metadata={
            "hallucination_detected": hallucinated,
            "tool_confirmed_not_found": tool_returned_not_found,
        },
    )


# ============================================================
# SCORER 4: Factuality (LLM-as-a-judge, autoevals built-in)
# ============================================================
# Used directly — Factuality compares output against expected answer.


# ============================================================
# SCORER 5: Policy compliance (custom LLM-as-a-judge)
# ============================================================
policy_compliance = LLMClassifier(
    name="PolicyCompliance",
    prompt_template="""You are auditing a customer support agent's response for policy compliance.

The customer asked: {{input}}
The agent responded: {{output}}
The correct answer is: {{expected}}

Evaluate whether the agent's response:
1. Accurately reflects the information returned by internal tools (does not fabricate data)
2. Correctly communicates refund eligibility (only delivered orders are refundable)
3. Does not promise actions that were not actually completed

Is the agent's response policy-compliant?""",
    choice_scores={"Yes": 1, "No": 0},
    use_cot=True,
)


# ============================================================
# SCORER 6: Answer quality (LLM-as-a-judge, autoevals ClosedQA)
# ============================================================
answer_quality = ClosedQA(
    criteria="Is the response helpful, accurate, and does it address the customer's specific question without providing incorrect information?"
)


# ============================================================
# RUN THE EVAL
# ============================================================
Eval(
    "Evals-101-Workshop",
    data=init_dataset(project="Evals-101-Workshop", name="support-agent-dataset"),
    task=task,
    scores=[
        keyword_match,
        correct_tool_used,
        no_hallucination_on_missing_order,
        Factuality,
        policy_compliance,
        answer_quality,
    ],
)
