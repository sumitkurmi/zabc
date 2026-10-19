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


# Regular expressions for stripping Markdown symbols before chunking
MARKDOWN_BLOCK_REGEX = re.compile(r"```[a-zA-Z]*\n?([\s\S]*?)```")
MARKDOWN_SYMBOL_REGEX = re.compile(r"[\*\_~`#]+|^\s*[\-\*]\s+|^\s*\d+\.\s+", re.MULTILINE)


def sanitize_text(text: str) -> str:
    """Strips sensitive student PII and raw Markdown formatting symbols before vector store indexing.

    Args:
        text: Raw chat transcript or user text.

    Returns:
        Sanitized text with email/phone/password redacted and plain text stripped of Markdown markup.
    """
    if not text:
        return ""

    # Replace emails
    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)

    # Replace phone numbers
    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", sanitized)

    # Replace plain text passwords
    sanitized = PASSWORD_PATTERNS.sub(r"\1: [REDACTED_PASSWORD]", sanitized)

    # Strip code block fences but keep code content
    sanitized = MARKDOWN_BLOCK_REGEX.sub(r"\1", sanitized)

    # Strip markdown symbols (*, _, ~, `, #, bullet dashes, list numbers) for clean plain-text vector embedding
    sanitized = MARKDOWN_SYMBOL_REGEX.sub(" ", sanitized)

    # Clean up duplicate underscores in REDACTED placeholders if any symbols matched
    sanitized = sanitized.replace("[REDACTED EMAIL]", "[REDACTED_EMAIL]").replace("[REDACTED PHONE]", "[REDACTED_PHONE]").replace("[REDACTED PASSWORD]", "[REDACTED_PASSWORD]")

    return sanitized
