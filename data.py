"""Shared fake data for the Acme Corp customer support agent.

Both start/ and solution/ agent files import from here so you can
focus on the agent logic and evals, not the test fixtures.
"""

# --- Order database ---
ORDERS = {
    "ORD-1001": {"status": "delivered", "items": ["Pro Plan (Annual)"], "total": 299.99, "date": "2025-01-15"},
    "ORD-1002": {"status": "shipped", "items": ["Team Plan (Monthly)"], "total": 49.99, "date": "2025-02-01"},
    "ORD-1003": {"status": "processing", "items": ["Enterprise Add-on"], "total": 999.00, "date": "2025-02-10"},
    "ORD-1004": {"status": "delivered", "items": ["Pro Plan (Monthly)", "Storage Upgrade"], "total": 74.98, "date": "2024-12-20"},
    "ORD-1005": {"status": "cancelled", "items": ["Starter Plan"], "total": 0.00, "date": "2025-01-05"},
}

# --- FAQ knowledge base ---
FAQS = [
    {"question": "How do I reset my password?", "answer": "Go to Settings > Security > Reset Password. You'll receive an email with a reset link."},
    {"question": "What payment methods do you accept?", "answer": "We accept Visa, Mastercard, American Express, and PayPal."},
    {"question": "How do I cancel my subscription?", "answer": "Go to Settings > Billing > Cancel Subscription. Your access continues until the end of your billing period."},
    {"question": "What is your refund policy?", "answer": "We offer full refunds on delivered orders within 30 days. Orders that are shipped or processing cannot be refunded until delivered."},
    {"question": "How do I contact support?", "answer": "Email support@acme.com or use the chat widget in the bottom-right corner of the app."},
    {"question": "Do you offer a free trial?", "answer": "Yes! All plans include a 14-day free trial. No credit card required."},
]
