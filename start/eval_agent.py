# TODO 1: Import what you need
# Hint: from autoevals import Factuality, ClosedQA, LLMClassifier, Score
# Hint: from braintrust import Eval, init_dataset
# Hint: from agent import support_agent

from agent import support_agent


# ============================================================
# TASK: Wrap the agent for eval
# ============================================================
# TODO 2: Define a task function that takes (input, hooks) and calls your agent
# Hint:
# def task(input, hooks):
#     return support_agent(input)


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
# Hint: Use init_dataset to load the dataset from Braintrust, and pass your task function directly
# Eval(
#     "Evals-101-Workshop",
#     data=init_dataset(project="Evals-101-Workshop", name="support-agent-dataset"),
#     task=task,
#     scores=[
#         # your scorers here
#     ],
# )
