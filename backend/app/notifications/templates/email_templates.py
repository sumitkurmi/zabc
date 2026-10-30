# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Email HTML and plain-text templates for complaint lifecycle notification triggers.

def render_template(template_name: str, context: dict) -> tuple[str, str, str]:
    """Renders plain text and HTML body pair for a named email template.

    Args:
        template_name: Email event template key.
        context: Template placeholder values dictionary.

    Returns:
        Tuple of (subject_text, text_body, html_body).
    """
    ticket_id = context.get("ticket_id", "N/A")
    name = context.get("name", "Student")
    public_url = context.get("public_url", "http://localhost:5173")

    if template_name == "otp_request":
        otp_code = context.get("otp_code", "")
        subject = f"[MNNIT Network] Your OTP Verification Code: {otp_code}"
        text = f"Dear {name},\n\nYour OTP code for network complaint registration is: {otp_code}\nThis code expires in 10 minutes.\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>MNNIT Network OTP Verification</h2>
<p>Dear <b>{name}</b>,</p>
<p>Your OTP verification code for complaint registration is:</p>
<h1 style="font-size: 32px; letter-spacing: 4px; color: #0284c7; font-family: monospace;">{otp_code}</h1>
<p>This code is valid for 10 minutes. Please do not share it with anyone.</p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "complaint_registered":
        subject = f"[MNNIT Network] Complaint Registered - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nYour complaint (Ticket #{ticket_id}) has been registered.\nProblem Type: {context.get('problem_type')}\nLocation: {context.get('location')}\n\nYou will receive email updates as technicians are assigned.\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>MNNIT IT Services Complaint Registration</h2>
<p>Dear <b>{name}</b>,</p>
<p>Your network complaint has been registered under <b>Ticket #{ticket_id}</b>.</p>
<ul>
  <li><b>Problem Type:</b> {context.get('problem_type')}</li>
  <li><b>Location:</b> {context.get('location')} ({context.get('address_room')})</li>
  <li><b>Registered At:</b> {context.get('created_at')}</li>
</ul>
<p>Our team is reviewing your ticket and will assign a technician shortly.</p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "complaint_assigned":
        tech_name = context.get("technician_name", "Network Technician")
        subject = f"[MNNIT Network] Technician Assigned - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nTechnician {tech_name} has been assigned to your complaint (Ticket #{ticket_id}).\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Technician Assigned</h2>
<p>Dear <b>{name}</b>,</p>
<p>Technician <b>{tech_name}</b> has been assigned to investigate your complaint (<b>Ticket #{ticket_id}</b>).</p>
<p>They will contact or visit your specified room within preferred hours.</p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "complaint_reassigned":
        tech_name = context.get("technician_name", "Network Technician")
        subject = f"[MNNIT Network] Complaint Reassigned - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nYour complaint (Ticket #{ticket_id}) has been reassigned to Technician {tech_name}.\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Complaint Reassigned</h2>
<p>Dear <b>{name}</b>,</p>
<p>Your complaint <b>Ticket #{ticket_id}</b> has been reassigned to Technician <b>{tech_name}</b>.</p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "complaint_solved":
        confirm_link = f"{public_url}/confirm/{context.get('confirm_token')}"
        subject = f"[MNNIT Network] Action Taken / Confirmation Required - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nTechnician {context.get('technician_name')} has resolved your complaint (Ticket #{ticket_id}).\n\nDiagnosis: {context.get('diagnosis')}\nSolution: {context.get('solution')}\n\nPlease confirm if your issue is resolved:\n{confirm_link}\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Action Taken on Ticket #{ticket_id}</h2>
<p>Dear <b>{name}</b>,</p>
<p>Technician <b>{context.get('technician_name')}</b> has completed resolution work on your complaint.</p>
<div style="background: #f8fafc; padding: 12px; border-radius: 8px; border-left: 4px solid #0284c7;">
  <p><b>Diagnosis:</b> {context.get('diagnosis')}</p>
  <p><b>Solution:</b> {context.get('solution')}</p>
</div>
<p style="margin-top: 16px;"><b>Please click below to confirm resolution:</b></p>
<p><a href="{confirm_link}" style="background: #0284c7; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: bold;">Confirm Resolution Status</a></p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "complaint_closed":
        subject = f"[MNNIT Network] Ticket Closed - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nYour complaint (Ticket #{ticket_id}) has been closed ({context.get('closed_by_text')}).\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Ticket Closed</h2>
<p>Dear <b>{name}</b>,</p>
<p>Your complaint <b>Ticket #{ticket_id}</b> has been closed ({context.get('closed_by_text')}).</p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "rating_request":
        rate_link = f"{public_url}/rate/{context.get('rate_token')}"
        subject = f"[MNNIT Network] Rate Service Quality - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nPlease rate the service provided by Technician {context.get('technician_name')} for Ticket #{ticket_id}:\n{rate_link}\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Service Rating Request</h2>
<p>Dear <b>{name}</b>,</p>
<p>Please share your feedback regarding Technician <b>{context.get('technician_name')}</b> for <b>Ticket #{ticket_id}</b>:</p>
<p><a href="{rate_link}" style="background: #d97706; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: bold;">Rate IT Service Quality</a></p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    elif template_name == "rating_received":
        subject = f"[MNNIT Network] Rating Received - Ticket #{ticket_id}"
        text = f"Rating: {context.get('rating')}/5 stars\nFeedback: {context.get('feedback') or 'None'}"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Student Rating Received</h2>
<p>Ticket #{ticket_id}: Received <b>{context.get('rating')} / 5 stars</b>.</p>
<p><b>Feedback:</b> {context.get('feedback') or 'No written feedback provided.'}</p>
</body></html>"""

    elif template_name == "complaint_reopened":
        subject = f"[MNNIT Network] Complaint Reopened - Ticket #{ticket_id}"
        text = f"Dear {name},\n\nYour complaint (Ticket #{ticket_id}) has been reopened and returned to the assigned technician.\n\nIT Services, MNNIT Allahabad"
        html = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
<h2>Complaint Reopened</h2>
<p>Dear <b>{name}</b>,</p>
<p>Your complaint <b>Ticket #{ticket_id}</b> has been reopened following your response. Our team will re-investigate the issue.</p>
<br><p>Regards,<br>IT Services Team, MNNIT Allahabad</p>
</body></html>"""

    else:
        subject = f"[MNNIT Network] Update on Ticket #{ticket_id}"
        text = f"Update regarding Ticket #{ticket_id}."
        html = f"<p>Update regarding Ticket #{ticket_id}.</p>"

    return subject, text, html
