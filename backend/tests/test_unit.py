"""Unit tests for chunker, sanitizer, parsers, and category mapping.

Specification Section 15.
"""

import os
import pytest
from backend.app.models import ProblemType
from backend.app.services.chunker import chunk_text
from backend.app.services.sanitizer import sanitize_text
from backend.app.services.category_map import map_symptom_to_category
from backend.app.services.parsers import parse_txt, format_chat_transcript


def test_chunk_text_basic():
    text = "Sentence 1. " * 50  # ~600 chars
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    assert len(chunks) >= 2
    assert all(len(c) <= 350 for c in chunks)


def test_sanitize_text_pii_redaction():
    raw_text = "Student email student@mnnit.ac.in and phone +919876543210 with password: mysecretpassword123 in Room 214."
    sanitized = sanitize_text(raw_text)

    assert "student@mnnit.ac.in" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "+919876543210" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "mysecretpassword123" not in sanitized
    assert "[REDACTED_PASSWORD]" in sanitized


def test_symptom_category_mapping():
    assert map_symptom_to_category("Hostel Wi-Fi is weak and disconnecting") == ProblemType.WIFI_PROBLEM
    assert map_symptom_to_category("Cannot get an IP address from DHCP") == ProblemType.IP_ADDRESS_ISSUE
    assert map_symptom_to_category("Browser shows proxy error port 8080") == ProblemType.PROXY_ISSUE
    assert map_symptom_to_category("Wall socket LAN port is broken and bent") == ProblemType.LAN_PORT_BROKEN
    assert map_symptom_to_category("Wired LAN connection is extremely slow") == ProblemType.LAN_PROBLEM


def test_format_chat_transcript():
    messages = [
        {"role": "user", "content": "Wi-Fi is down"},
        {"role": "assistant", "content": "Please try forgetting the network"}
    ]
    formatted = format_chat_transcript(messages, "2026-03-31")
    assert "--- Chat Transcript (2026-03-31) ---" in formatted
    assert "Student: Wi-Fi is down" in formatted
    assert "Assistant: Please try forgetting the network" in formatted
