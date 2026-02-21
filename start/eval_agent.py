# TODO 1: Import what you need
# Hint: from autoevals import LLMClassifier, Score
# Hint: from autoevals.ragas import Faithfulness
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
# SCORER 1: Brand guidelines (custom LLM-as-a-judge)
# ============================================================
# TODO 3: Build an LLMClassifier that checks brand voice compliance
# - Acme Corp is a project management SaaS company
# - Brand voice: concise, friendly, professional, empathetic, honest, solution-oriented
# - Only use {{input}} and {{output}} in the template (not {{expected}})
# - This is about HOW the agent communicates, not factual accuracy
#
# Hint:
# brand_guidelines = LLMClassifier(
#     name="BrandGuidelines",
#     prompt_template="""...""",
#     choice_scores={"Yes": 1, "No": 0},
#     use_cot=True,
# )


# ============================================================
# SCORER 2: Faithfulness (RAGAS, trace-based context extraction)
# ============================================================
# TODO 4: Build an async scorer that checks if the agent's output
# is grounded in what the tools actually returned
# - Create a module-level instance: _faithfulness_scorer = Faithfulness()
# - Must be async! Use trace.get_spans(span_type=["tool"]) to get tool spans
# - Join all tool outputs into a single context string
# - Call: await _faithfulness_scorer.eval_async(output=output, expected=output, input=input, context=context)
# - If no trace or no tool outputs, return Score(name="Faithfulness", score=0, metadata={...})
#
# Hint:
# _faithfulness_scorer = Faithfulness()
#
# async def faithfulness(input, output, expected, trace=None, **kwargs):
#     tool_spans = await trace.get_spans(span_type=["tool"])
#     tool_outputs = [f"{s['name']}: {s['output']}" for s in tool_spans if s.get("output")]
#     context = "\n".join(tool_outputs)
#     return await _faithfulness_scorer.eval_async(output=output, expected=output, input=input, context=context)


# ============================================================
# SCORER 3: Expected tool call path (trace-based, sequence check)
# ============================================================
# TODO 5: Build an async scorer that checks the ORDER of tool calls
# - Read metadata["expected_tool_path"] — a list of tool names in order
# - Use trace.get_spans(span_type=["tool"]) to get tool spans in order
# - Compare the actual path (list) to the expected path (list) with ==
# - Return None if metadata doesn't have expected_tool_path (skip)
#
# Hint:
# async def expected_tool_path(input, output, expected, metadata=None, trace=None, **kwargs):
#     target_path = metadata["expected_tool_path"]
#     tool_spans = await trace.get_spans(span_type=["tool"])
#     actual_path = [s.get("name") for s in tool_spans]
#     match = actual_path == target_path
#     return Score(name="expected_tool_path", score=1 if match else 0, metadata={...})


# ============================================================
# RUN THE EVAL
# ============================================================
# TODO 6: Wire it all together
# Hint: Use init_dataset to load the dataset from Braintrust, and pass your task function directly
# Eval(
#     "Evals-101-Workshop",
#     data=init_dataset(project="Evals-101-Workshop", name="support-agent-dataset"),
#     task=task,
#     scores=[
#         # your 3 scorers here
#     ],
# )
