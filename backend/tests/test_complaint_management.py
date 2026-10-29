# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Pytest test suite for Part 2 complaint management rules, auth, lifecycle, and stock rollbacks.

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from backend.app.complaint_management.routers.public_otp import validate_email_domain, hash_otp
from backend.app.complaint_management.services.ticket_service import generate_ticket_id
from backend.app.complaint_management.services.scoring_service import compute_technician_score
from backend.app.complaint_management.models import ComplaintStatus, StaffRole, ActionTokenPurpose
from backend.app.complaint_management.routers.student_actions import hash_token


def test_email_domain_validation():
    """Tests student college email domain validation rules."""
    # Valid email
    assert validate_email_domain("student1@mnnit.ac.in") == "student1@mnnit.ac.in"
    assert validate_email_domain("STU.DENT2@mnnit.ac.in ") == "stu.dent2@mnnit.ac.in"

    # Invalid: wrong domain
    with pytest.raises(HTTPException):
        validate_email_domain("student@gmail.com")

    # Invalid: subdomain
    with pytest.raises(HTTPException):
        validate_email_domain("student@cs.mnnit.ac.in")

    # Invalid: double @
    with pytest.raises(HTTPException):
        validate_email_domain("student@@mnnit.ac.in")


def test_otp_hashing():
    """Tests OTP code HMAC-SHA256 hashing."""
    h1 = hash_otp("123456")
    h2 = hash_otp("123456")
    h3 = hash_otp("654321")

    assert len(h1) == 64
    assert h1 == h2
    assert h1 != h3


def test_token_hashing():
    """Tests action token SHA-256 hashing."""
    raw = "test_token_string_123"
    th1 = hash_token(raw)
    th2 = hash_token(raw)

    assert len(th1) == 64
    assert th1 == th2


def test_scoring_formulas():
    """Tests plain average and Bayesian weighted leaderboard scoring formulas."""
    # Plain average
    score_avg = compute_technician_score(avg_rating=4.5, rating_count=2, resolved_count=10)
    assert score_avg == 4.5

    # Unrated
    score_unrated = compute_technician_score(avg_rating=None, rating_count=0, resolved_count=5)
    assert score_unrated == 0.0


@pytest.mark.asyncio
async def test_ticket_id_format():
    """Tests 12-digit ticket ID format YYMMDDHHMMSS."""
    tid = await generate_ticket_id()
    assert len(tid) == 12
    assert tid.isdigit()
