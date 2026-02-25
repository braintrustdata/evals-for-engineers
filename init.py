"""Initialize the Braintrust project with the workshop dataset.

Run this once before the workshop to set up the Evals-101-Workshop project
and populate its dataset with the 12 test cases used in the eval.

Usage:
    uv run python init.py
"""

import braintrust
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_NAME = "Evals-101-Workshop"
DATASET_NAME = "support-agent-dataset"

DATASET = [
    # --- Happy path: order lookup ---
    {
        "input": "What's the status of order ORD-1001?",
        "expected": "Order ORD-1001 has been delivered. It contains Pro Plan (Annual) and the total was $299.99.",
        "metadata": {"category": "order_lookup", "expected_tool": "lookup_order", "expected_tool_path": ["lookup_order"]},
    },
    {
        "input": "Can you tell me about order ORD-1004?",
        "expected": "Order ORD-1004 has been delivered. Items: Pro Plan (Monthly) and Storage Upgrade. Total: $74.98.",
        "metadata": {"category": "order_lookup", "expected_tool": "lookup_order", "expected_tool_path": ["lookup_order"]},
    },
    # --- Happy path: refund (eligible) ---
    {
        "input": "I'd like a refund for order ORD-1001, the product didn't meet my expectations.",
        "expected": "Refund of $299.99 for order ORD-1001 has been processed.",
        "metadata": {"category": "refund", "expected_tool": "process_refund", "expected_tool_path": ["process_refund"]},
    },
    # --- Happy path: FAQ ---
    {
        "input": "How do I reset my password?",
        "expected": "Go to Settings > Security > Reset Password. You'll receive an email with a reset link.",
        "metadata": {"category": "faq", "expected_tool": "search_faq", "expected_tool_path": ["search_faq"]},
    },
    {
        "input": "What payment methods do you accept?",
        "expected": "We accept Visa, Mastercard, American Express, and PayPal.",
        "metadata": {"category": "faq", "expected_tool": "search_faq", "expected_tool_path": ["search_faq"]},
    },
    # --- Failure mode 1: Hallucinated order data (nonexistent order) ---
    {
        "input": "What's the status of order ORD-9999?",
        "expected": "Order ORD-9999 was not found. Please double-check your order ID or contact support.",
        "metadata": {"category": "order_not_found", "expected_tool": "lookup_order", "expected_tool_path": ["lookup_order"]},
    },
    {
        "input": "Tell me about order ORD-0000",
        "expected": "That order could not be found in our system.",
        "metadata": {"category": "order_not_found", "expected_tool": "lookup_order", "expected_tool_path": ["lookup_order"]},
    },
    # --- Failure mode 2: Wrong tool selection ---
    {
        "input": "Do you offer a free trial?",
        "expected": "Yes! All plans include a 14-day free trial. No credit card required.",
        "metadata": {"category": "faq", "expected_tool": "search_faq", "expected_tool_path": ["search_faq"]},
    },
    {
        "input": "How do I cancel my subscription?",
        "expected": "Go to Settings > Billing > Cancel Subscription. Your access continues until the end of your billing period.",
        "metadata": {"category": "faq", "expected_tool": "search_faq", "expected_tool_path": ["search_faq"]},
    },
    # --- Failure mode 3: Refund policy violation (ineligible orders) ---
    {
        "input": "I want a refund for order ORD-1002",
        "expected": "Order ORD-1002 is currently shipped and is not eligible for a refund. Only delivered orders can be refunded.",
        "metadata": {"category": "refund_ineligible", "expected_tool": "process_refund", "expected_tool_path": ["process_refund"]},
    },
    {
        "input": "Please refund order ORD-1003, I changed my mind.",
        "expected": "Order ORD-1003 is still processing and cannot be refunded yet. Only delivered orders are eligible.",
        "metadata": {"category": "refund_ineligible", "expected_tool": "process_refund", "expected_tool_path": ["process_refund"]},
    },
    # --- Failure mode 4: FAQ mismatch ---
    {
        "input": "Can I integrate Acme with Slack?",
        "expected": "I don't have information about Slack integration. Please contact support@acme.com for help.",
        "metadata": {"category": "faq_no_match", "expected_tool": "search_faq", "expected_tool_path": ["search_faq"]},
    },
]


def main():
    dataset = braintrust.init_dataset(project=PROJECT_NAME, name=DATASET_NAME, api_key=os.environ["BRAINTRUST_API_KEY"])

    for row in DATASET:
        dataset.insert(
            input=row["input"],
            expected=row["expected"],
            metadata=row["metadata"],
        )

    dataset.flush()
    print(f"Loaded {len(DATASET)} rows into dataset '{DATASET_NAME}' in project '{PROJECT_NAME}'")


if __name__ == "__main__":
    main()
