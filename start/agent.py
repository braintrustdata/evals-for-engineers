import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI

from data import FAQS, ORDERS

# TODO 1: Import tracing utilities from braintrust
# Hint: you need traced, init_logger, wrap_openai, and current_span
# from braintrust import ...

# TODO 2: Initialize the Braintrust logger
# Hint: logger = init_logger(project="...")

# TODO 3: Wrap the OpenAI client for automatic tracing
# Hint: client = wrap_openai(OpenAI())
client = OpenAI()


# --- Tool implementations ---

# TODO 4: Add @traced decorator to each tool function

def lookup_order(order_id: str) -> str:
    """Look up an order by ID. Returns JSON with order details or 'not found'."""
    # TODO 5: Implement this function
    # - Look up order_id in the ORDERS dict
    # - If not found, return f"Order {order_id} not found."
    # - If found, return json.dumps({"order_id": order_id, **order})
    pass


def process_refund(order_id: str, reason: str) -> str:
    """Process a refund. Only delivered orders are eligible."""
    # TODO 6: Implement this function
    # - Look up the order
    # - If not found, return an error
    # - If status != "delivered", return an error explaining it's not eligible
    # - Otherwise, return a success message with the refund amount
    pass


def search_faq(query: str) -> str:
    """Search FAQs using keyword matching."""
    # TODO 7: Implement this function
    # - Split the query into words, filter to words > 3 chars
    # - Loop through FAQS and check if any query word appears in the FAQ question
    # - Return the first match as JSON, or a "no match" response
    pass


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

# TODO 8: Add @traced decorator
def support_agent(user_message: str) -> str:
    """Run the support agent with an agentic tool-calling loop."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    # TODO 9: Implement the agentic loop
    # - Call client.chat.completions.create() with model, messages, and tools
    # - Check if finish_reason == "stop" → return the message content
    # - Otherwise, process each tool_call:
    #     - Parse the function name and arguments
    #     - Call the tool via TOOL_MAP
    #     - Append the tool result to messages
    # - Loop up to 3 times to allow multi-step tool use
    # - After the loop, make one final call to get the answer

    pass


# --- Manual testing ---
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
