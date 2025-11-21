"""Email sender tool with SMTP support."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
import os

from craft.tools import tool


@tool
def send_email(
    to: str,
    subject: str,
    body: str,
    from_addr: Optional[str] = None,
    smtp_config: Optional[Dict[str, Any]] = None,
    html: bool = False,
) -> bool:
    """
    Send email via SMTP with template support.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        from_addr: Sender email address (optional, uses SMTP_FROM_ADDR env var)
        smtp_config: SMTP configuration dict (optional, uses env vars)
        html: Whether body is HTML (default: False)

    Returns:
        True if email sent successfully

    SMTP Configuration (via smtp_config or environment variables):
        - host: SMTP server host (SMTP_HOST)
        - port: SMTP server port (SMTP_PORT, default: 587)
        - username: SMTP username (SMTP_USERNAME)
        - password: SMTP password (SMTP_PASSWORD)
        - use_tls: Use TLS (SMTP_USE_TLS, default: True)

    Example:
        send_email(
            to="user@example.com",
            subject="Hello",
            body="<h1>Hello World</h1>",
            html=True
        )
    """
    # Get SMTP configuration
    if smtp_config is None:
        smtp_config = {
            "host": os.getenv("SMTP_HOST", "localhost"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME"),
            "password": os.getenv("SMTP_PASSWORD"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        }

    from_addr = from_addr or os.getenv("SMTP_FROM_ADDR")
    if not from_addr:
        raise ValueError("Sender email address required (from_addr or SMTP_FROM_ADDR)")

    # Create message
    msg = MIMEMultipart("alternative") if html else MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    if html:
        # Add both plain text and HTML versions
        part1 = MIMEText(body, "plain")
        part2 = MIMEText(body, "html")
        msg.attach(part1)
        msg.attach(part2)

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])

        if smtp_config.get("use_tls"):
            server.starttls()

        # Login if credentials provided
        if smtp_config.get("username") and smtp_config.get("password"):
            server.login(smtp_config["username"], smtp_config["password"])

        # Send email
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
