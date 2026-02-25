import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from braintrust import init_logger, traced, wrap_openai
from openai import OpenAI

from data import FAQS, ORDERS

from dotenv import load_dotenv

load_dotenv()

# --- Initialize tracing ---
logger = init_logger(project="Evals-101-Workshop")
client = wrap_openai(
    OpenAI(
        api_key=os.environ["OPENAI_API_KEY"]
    )
)


# --- Tool implementations ---

@traced(type="tool")
def lookup_order(order_id: str) -> str:
    order = ORDERS.get(order_id)
    if not order:
        return f"Order {order_id} not found."
    return json.dumps({"order_id": order_id, **order})


@traced(type="tool")
def process_refund(order_id: str, reason: str) -> str:
    order = ORDERS.get(order_id)
    if not order:
        return f"Error: Order {order_id} not found."
    if order["status"] != "delivered":
        return f"Error: Order {order_id} is '{order['status']}' and is not eligible for a refund. Only delivered orders can be refunded."
    return f"Refund of ${order['total']:.2f} for order {order_id} has been processed. Reason: {reason}"


@traced(type="tool")
def search_faq(query: str) -> str:
    query_lower = query.lower()
    for faq in FAQS:
        if any(word in faq["question"].lower() for word in query_lower.split() if len(word) > 3):
            return json.dumps(faq)
    return json.dumps({"question": "No match", "answer": "I couldn't find a relevant FAQ entry. Please contact support@acme.com."})


# --- Tool dispatch ---
TOOL_MAP = {
    "lookup_order": lambda args: lookup_order(**args),
    "process_refund": lambda args: process_refund(**args),
    "search_faq": lambda args: search_faq(**args),
}

# --- OpenAI tool schemas ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": "Look up an order by its order ID. Returns order details including status, items, and total.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order ID, e.g. ORD-1001"}},
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund for an order. Only delivered orders are eligible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to refund"},
                    "reason": {"type": "string", "description": "Reason for the refund"},
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_faq",
            "description": "Search the FAQ knowledge base for product questions about billing, accounts, features, etc.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "The search query"}},
                "required": ["query"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a helpful customer support agent for Acme Corp, a project management SaaS product.
Use the provided tools to help customers with their questions. Be concise and friendly.
If a tool returns an error, relay that information honestly to the customer — do not make up information."""


# --- Agent loop ---
@traced(type="task")
def support_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for _ in range(3):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
        )
        choice = response.choices[0]

        if choice.finish_reason == "stop":
            return choice.message.content

        # Process tool calls
        messages.append(choice.message)
        for tool_call in choice.message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            result = TOOL_MAP[fn_name](fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    # Exhausted tool-call rounds — get a final answer
    final = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return final.choices[0].message.content


# --- Manual testing / trace generation ---
if __name__ == "__main__":
    test_queries = [
        "What's the status of order ORD-1001?",
        "I want a refund for order ORD-1002",
        "How do I reset my password?",
        "What's the status of order ORD-9999?",
        "Can I integrate Acme with Slack?",
        "Please refund order ORD-1003, I changed my mind.",
    ]
    for q in test_queries:
        print(f"\nUser: {q}")
        print(f"Agent: {support_agent(q)}")
