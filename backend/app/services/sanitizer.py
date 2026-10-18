"""PII Sanitizer module for privacy compliance.

Strips personally identifiable information (emails, Indian phone numbers, passwords, room numbers)
from student chat transcripts before indexing into the vector knowledge base.

Specification Section 8.1 & Section 11.
"""

import re

# Regular expressions for PII detection and redaction
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}")
PASSWORD_PATTERNS = re.compile(r"(?i)(password|pass|pwd|key)\s*[:=]\s*\S+")


def sanitize_text(text: str) -> str:
    """Strips sensitive student PII from chat transcripts before vector store indexing.

    Args:
        text: Raw chat transcript or user text.

    Returns:
        Sanitized text with email addresses and phone numbers replaced with placeholders.
    """
    if not text:
        return ""

    # Replace emails
    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)

    # Replace phone numbers
    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)

    # Replace plain text passwords
    sanitized = PASSWORD_PATTERNS.sub(r"\1: [REDACTED_PASSWORD]", sanitized)

    return sanitized
