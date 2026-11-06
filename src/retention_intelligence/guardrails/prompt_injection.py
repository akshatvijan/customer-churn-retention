
import re


SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"show\s+(your\s+)?system\s+prompt",
    r"override\s+(all\s+)?instructions",
    r"bypass\s+(the\s+)?security",
    r"disable\s+(the\s+)?guardrails",
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"approve\s+all\s+rewards\s+automatically"
]


def detect_prompt_injection(text: str) -> dict:

    if not isinstance(text, str):
        return {
            "is_suspicious": True,
            "status": "rejected",
            "matched_patterns": [],
            "reason": "Input must be a string"
        }

    if not text.strip():
        return {
            "is_suspicious": False,
            "status": "safe",
            "matched_patterns": [],
            "reason": "Empty input"
        }

    matched_patterns = []

    for pattern in SUSPICIOUS_PATTERNS:

        if re.search(pattern, text, re.IGNORECASE):
            matched_patterns.append(pattern)

    if matched_patterns:
        return {
            "is_suspicious": True,
            "status": "requires_review",
            "matched_patterns": matched_patterns,
            "reason": "Potential prompt injection detected"
        }

    return {
        "is_suspicious": False,
        "status": "safe",
        "matched_patterns": [],
        "reason": "No known suspicious patterns detected"
    }
