# TODO 1: Import what you need
# Hint: from autoevals import Factuality, ClosedQA, LLMClassifier, Score
# Hint: from braintrust import Eval
# Hint: from agent import support_agent

from agent import support_agent

# ============================================================
# DATASET: Start with a few test cases, add more as you go
# ============================================================
DATASET = [
    # Happy path: order lookup
    {
        "input": "What's the status of order ORD-1001?",
        "expected": "Order ORD-1001 has been delivered. It contains Pro Plan (Annual) and the total was $299.99.",
        "metadata": {"category": "order_lookup", "expected_tool": "lookup_order"},
    },
    # Happy path: FAQ
    {
        "input": "How do I reset my password?",
        "expected": "Go to Settings > Security > Reset Password. You'll receive an email with a reset link.",
        "metadata": {"category": "faq", "expected_tool": "search_faq"},
    },
    # Failure mode: nonexistent order
    {
        "input": "What's the status of order ORD-9999?",
        "expected": "Order ORD-9999 was not found. Please double-check your order ID or contact support.",
        "metadata": {"category": "order_not_found", "expected_tool": "lookup_order"},
    },

    # TODO 2: Add more test cases! Think about:
    # - Another order lookup (ORD-1004)
    # - A refund for an eligible order (ORD-1001, status: delivered)
    # - A refund for an ineligible order (ORD-1002, status: shipped)
    # - A refund for another ineligible order (ORD-1003, status: processing)
    # - More FAQ questions (payment methods, free trial, cancel subscription)
    # - A question with no FAQ match (e.g., Slack integration)
]


# ============================================================
# SCORER 1: Keyword match (code-based)
# ============================================================
# TODO 3: Implement a keyword_match scorer
# - Extract words >= 4 chars from expected
# - Count how many appear in the output
# - Return Score(name="keyword_match", score=matches/total)
#
# def keyword_match(input, output, expected, **kwargs):
#     ...


# ============================================================
# SCORER 2: Tool usage checker (trace-based)
# ============================================================
# TODO 4: Implement a correct_tool_used scorer that inspects the trace
# - This scorer uses the `trace` parameter to access actual execution spans
# - Must be async! Use: async def correct_tool_used(input, output, expected, metadata=None, trace=None, **kwargs):
# - Call: all_spans = await trace.get_spans()
# - Each span has a "name" field — check if the expected tool appears in the span names
# - Return None if no expected_tool in metadata (skip this test case)
#
# Hint: tool_names_called = [s.get("name") for s in all_spans
#            if s.get("name") in ("lookup_order", "process_refund", "search_faq")]


# ============================================================
# SCORER 3: No-hallucination checker (trace-based)
# ============================================================
# TODO 5: Implement a no_hallucination_on_missing_order scorer
# - Only applies when metadata["category"] == "order_not_found"
# - Return None for all other categories (skip)
# - Must be async! Use the `trace` parameter to verify the tool returned "not found"
# - Also check if the final output contains hallucination signals like
#   "delivered", "shipped", "processing", "pro plan", etc.
# - Return score=0 if hallucinated, score=1 if clean
#
# Hint: inspect span output with:
#   all_spans = await trace.get_spans()
#   for span in all_spans:
#       if span.get("name") == "lookup_order":
#           span_output = str(span.get("output", ""))


# ============================================================
# SCORER 4: Factuality (LLM-as-a-judge)
# ============================================================
# TODO 6: Import and use autoevals.Factuality
# It works out of the box — just pass it to the scores list


# ============================================================
# SCORER 5: Policy compliance (custom LLM-as-a-judge)
# ============================================================
# TODO 7: Build a custom LLMClassifier
# Hint:
# policy_compliance = LLMClassifier(
#     name="PolicyCompliance",
#     prompt_template="""...""",   # Use {{input}}, {{output}}, {{expected}}
#     choice_scores={"Yes": 1, "No": 0},
#     use_cot=True,
# )


# ============================================================
# SCORER 6: Answer quality (LLM-as-a-judge)
# ============================================================
# TODO 8: Use autoevals.ClosedQA with a custom criteria string
# Hint: answer_quality = ClosedQA(criteria="...")


# ============================================================
# RUN THE EVAL
# ============================================================
# TODO 9: Wire it all together
# Eval(
#     "Evals-101-Workshop",
#     data=lambda: DATASET,
#     task=lambda input: support_agent(input),
#     scores=[
#         # your scorers here
#     ],
# )
