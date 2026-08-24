import re

try:
    import spacy
    _nlp = spacy.blank("en")
except Exception:
    _nlp = None

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if _nlp:
        doc = _nlp(text.lower())
        return " ".join(t.text for t in doc if not t.is_space)
    return text.lower()

def classify_intent(text: str) -> str:
    t = clean_text(text)

    rules = {
        "escalation": [
            "human", "agent", "manager", "representative",
            "speak to someone", "speak with someone"
        ],
        "complaint": [
            "complaint", "unhappy", "bad service",
            "terrible", "worst", "useless"
        ],
        "password": [
            "password", "reset password", "forgot password"
        ],
        "billing": [
            "bill", "billing", "invoice", "charged", "payment"
        ],
        "refund": [
            "refund", "money back", "return payment"
        ],
        "account": [
            "account", "profile", "email change"
        ],
        "technical": [
            "error", "bug", "not working", "crash", "failed", "issue"
        ],
        "shipping": [
            "shipping", "delivery", "deliver", "tracking", "order"
        ],
        "greeting": [
            "hello", "hi", "hey", "good morning", "good evening"
        ],
    }

    # Check longer/more important support intents first.
    for intent, phrases in rules.items():
        for phrase in phrases:
            if " " in phrase:
                if phrase in t:
                    return intent
            else:
                if phrase in t.split():
                    return intent

    return "faq"

def detect_frustration(text: str) -> bool:
    t = clean_text(text)
    signals = ["angry", "ridiculous", "terrible", "worst", "useless", "hate", "not helping", "again and again", "!!!"]
    return sum(s in t for s in signals) >= 1

def is_prompt_injection(text: str) -> bool:
    t = clean_text(text)
    signals = [
        "ignore previous instructions", "ignore all instructions",
        "reveal your system prompt", "show your hidden prompt",
        "developer message", "jailbreak", "bypass your rules"
    ]
    return any(s in t for s in signals)
