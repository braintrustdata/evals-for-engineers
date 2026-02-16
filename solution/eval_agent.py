from autoevals import ClosedQA, Factuality, LLMClassifier, Score
from braintrust import Eval

from agent import support_agent

# ============================================================
# DATASET: 12 test cases covering happy paths + 4 failure modes
# ============================================================
DATASET = [
    # --- Happy path: order lookup ---
    {
        "input": "What's the status of order ORD-1001?",
        "expected": "Order ORD-1001 has been delivered. It contains Pro Plan (Annual) and the total was $299.99.",
        "metadata": {"category": "order_lookup", "expected_tool": "lookup_order"},
    },
    {
        "input": "Can you tell me about order ORD-1004?",
        "expected": "Order ORD-1004 has been delivered. Items: Pro Plan (Monthly) and Storage Upgrade. Total: $74.98.",
        "metadata": {"category": "order_lookup", "expected_tool": "lookup_order"},
    },
    # --- Happy path: refund (eligible) ---
    {
        "input": "I'd like a refund for order ORD-1001, the product didn't meet my expectations.",
        "expected": "Refund of $299.99 for order ORD-1001 has been processed.",
        "metadata": {"category": "refund", "expected_tool": "process_refund"},
    },
    # --- Happy path: FAQ ---
    {
        "input": "How do I reset my password?",
        "expected": "Go to Settings > Security > Reset Password. You'll receive an email with a reset link.",
        "metadata": {"category": "faq", "expected_tool": "search_faq"},
    },
    {
        "input": "What payment methods do you accept?",
        "expected": "We accept Visa, Mastercard, American Express, and PayPal.",
        "metadata": {"category": "faq", "expected_tool": "search_faq"},
    },
    # --- Failure mode 1: Hallucinated order data (nonexistent order) ---
    {
        "input": "What's the status of order ORD-9999?",
        "expected": "Order ORD-9999 was not found. Please double-check your order ID or contact support.",
        "metadata": {"category": "order_not_found", "expected_tool": "lookup_order"},
    },
    {
        "input": "Tell me about order ORD-0000",
        "expected": "That order could not be found in our system.",
        "metadata": {"category": "order_not_found", "expected_tool": "lookup_order"},
    },
    # --- Failure mode 2: Wrong tool selection ---
    {
        "input": "Do you offer a free trial?",
        "expected": "Yes! All plans include a 14-day free trial. No credit card required.",
        "metadata": {"category": "faq", "expected_tool": "search_faq"},
    },
    {
        "input": "How do I cancel my subscription?",
        "expected": "Go to Settings > Billing > Cancel Subscription. Your access continues until the end of your billing period.",
        "metadata": {"category": "faq", "expected_tool": "search_faq"},
    },
    # --- Failure mode 3: Refund policy violation (ineligible orders) ---
    {
        "input": "I want a refund for order ORD-1002",
        "expected": "Order ORD-1002 is currently shipped and is not eligible for a refund. Only delivered orders can be refunded.",
        "metadata": {"category": "refund_ineligible", "expected_tool": "process_refund"},
    },
    {
        "input": "Please refund order ORD-1003, I changed my mind.",
        "expected": "Order ORD-1003 is still processing and cannot be refunded yet. Only delivered orders are eligible.",
        "metadata": {"category": "refund_ineligible", "expected_tool": "process_refund"},
    },
    # --- Failure mode 4: FAQ mismatch ---
    {
        "input": "Can I integrate Acme with Slack?",
        "expected": "I don't have information about Slack integration. Please contact support@acme.com for help.",
        "metadata": {"category": "faq_no_match", "expected_tool": "search_faq"},
    },
]


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
    data=lambda: DATASET,
    task=lambda input: support_agent(input),
    scores=[
        keyword_match,
        correct_tool_used,
        no_hallucination_on_missing_order,
        Factuality,
        policy_compliance,
        answer_quality,
    ],
)
