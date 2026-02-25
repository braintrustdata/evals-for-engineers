from autoevals import LLMClassifier, Score
from autoevals.ragas import Faithfulness
from braintrust import Eval, init_dataset, _internal_get_global_state

from solution.agent import support_agent


# ============================================================
# TASK: Wrap the agent for eval
# ============================================================
def task(input, hooks):
    return support_agent(input)


# ============================================================
# SCORER 1: Brand guidelines (custom LLM-as-a-judge)
# ============================================================
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


# ============================================================
# SCORER 2: Faithfulness (RAGAS, trace-based context extraction)
# ============================================================
_faithfulness_scorer = Faithfulness()


async def faithfulness(input, output, expected, trace=None, **kwargs):
    """Check if the agent's output is grounded in the tool outputs (context).

    Extracts tool call outputs from the trace spans to use as context,
    then uses the RAGAS Faithfulness scorer to verify groundedness.
    """
    _internal_get_global_state().span_cache.disable()
    if not trace:
        return Score(name="Faithfulness", score=0, metadata={"reason": "no trace available"})

    # Extract tool outputs from trace spans as context
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

    result = await _faithfulness_scorer.eval_async(
        output=output,
        expected=output,
        input=input,
        context=context,
    )
    return result


# ============================================================
# SCORER 3: Expected tool call path (trace-based, sequence check)
# ============================================================
async def expected_tool_path(input, output, expected, metadata=None, trace=None, **kwargs):
    """Check if the agent called tools in the expected order.

    Compares the actual sequence of tool calls (from trace spans)
    against the expected_tool_path in metadata.
    """
    _internal_get_global_state().span_cache.disable()
    if not metadata or "expected_tool_path" not in metadata:
        return None

    target_path = set(metadata["expected_tool_path"])

    if not trace:
        return Score(name="expected_tool_path", score=0, metadata={"reason": "no trace"})

    # Get tool spans in order and extract the call sequence
    tool_spans = await trace.get_spans(span_type=["tool"])
    actual_path = set([s.span_attributes.get("name") for s in tool_spans])

    match = actual_path == target_path
    return Score(
        name="expected_tool_path",
        score=1 if match else 0,
        metadata={
            "expected_path": target_path,
            "actual_path": actual_path,
        },
    )


# ============================================================
# RUN THE EVAL
# ============================================================
Eval(
    "Evals-101-Workshop",
    data=init_dataset(project="Evals-101-Workshop", name="support-agent-dataset"),
    task=task,
    scores=[
        brand_guidelines,
        faithfulness,
        expected_tool_path,
    ],
)
