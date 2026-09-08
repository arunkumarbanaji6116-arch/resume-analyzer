import json
import logging
import os
import smtplib
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from config import Config

logger = logging.getLogger("careerforge.email")


def _get_resend_key() -> str:
    """Dynamically get Resend API key from environment or config."""
    import os
    return (
        os.getenv("RESEND_API_KEY", "").strip()
        or os.getenv("RESEND_KEY", "").strip()
        or os.getenv("RESEND_API", "").strip()
        or getattr(Config, "RESEND_API_KEY", "")
    ).strip()


def is_resend_configured() -> bool:
    """Check if Resend API key is configured."""
    return bool(_get_resend_key())


def is_smtp_configured() -> bool:
    """Check if valid SMTP authentication credentials are provided."""
    return bool(Config.SMTP_USER and Config.SMTP_PASSWORD)


def _build_otp_templates(clean_code: str) -> tuple[str, str]:
    """Builds plain-text and rich HTML templates for Google OTP verification."""
    plain_text = f"""CareerForge.AI · Career Development Platform
Continue with Google Verification

Use the following 6-digit verification code to complete your sign-in:

{clean_code}

This code expires in 30 minutes. If you did not request this code, please ignore this email.

— The CareerForge.AI Team
"""

    html_content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CareerForge.AI Verification · Career Development Platform</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0b0f19;
      color: #f1f5f9;
      margin: 0;
      padding: 32px 16px;
    }}
    .wrapper {{
      max-width: 520px;
      margin: 0 auto;
      background: #111827;
      border: 1px solid #1f2937;
      border-radius: 16px;
      padding: 36px 28px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }}
    .brand {{
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #ffffff;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .brand span {{
      color: #4f46e5;
    }}
    .google-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 20px;
      background: #1e293b;
      font-size: 12px;
      font-weight: 600;
      color: #94a3b8;
      margin-bottom: 16px;
    }}
    h1 {{
      font-size: 22px;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 10px 0;
    }}
    p {{
      font-size: 14px;
      line-height: 1.6;
      color: #94a3b8;
      margin: 0 0 20px 0;
    }}
    .otp-box {{
      background: #1e1b4b;
      border: 1px solid #4338ca;
      border-radius: 12px;
      padding: 18px 24px;
      text-align: center;
      margin: 24px 0;
    }}
    .otp-code {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #a5b4fc;
      margin: 0;
    }}
    .footer {{
      margin-top: 28px;
      padding-top: 20px;
      border-top: 1px solid #1f2937;
      font-size: 12px;
      color: #64748b;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="brand">
      CareerForge.<span>AI</span>
    </div>
    <div class="google-badge">
      <svg width="14" height="14" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.66v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.15z"/>
        <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.94H1.24v3.15C3.26 21.36 7.34 24 12 24z"/>
        <path fill="#FBBC05" d="M5.28 14.26c-.25-.72-.38-1.49-.38-2.26s.13-1.54.38-2.26V6.59H1.24C.45 8.16 0 9.92 0 12s.45 3.84 1.24 5.41l4.04-3.15z"/>
        <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.24 6.59l4.04 3.15c.95-2.84 3.6-4.99 6.72-4.99z"/>
      </svg>
      <span>Google Verification</span>
    </div>
    <h1>Verify your Google Account</h1>
    <p>You requested to continue with Google on CareerForge.AI (Career Development Platform). Use the verification code below to securely complete your sign-in:</p>
    
    <div class="otp-box">
      <div class="otp-code">{clean_code}</div>
    </div>
    
    <p style="font-size: 13px; color: #cbd5e1;">This code is valid for <strong>30 minutes</strong>. Do not share this code with anyone.</p>
    <p style="font-size: 12px; color: #64748b;">If you did not initiate this request, you can safely ignore this email.</p>
    
    <div class="footer">
      Sent by CareerForge.AI &bull; Career Development Platform
    </div>
  </div>
</body>
</html>
"""
    return plain_text, html_content


def send_via_resend(recipient: str, subject: str, html_content: str, plain_text: str) -> tuple[bool, str]:
    """
    Sends an email using Resend's REST API (https://api.resend.com/emails).
    """
    api_key = _get_resend_key()
    from_email = os.getenv("RESEND_FROM_EMAIL", "").strip() or Config.RESEND_FROM_EMAIL or "CareerForge.AI <onboarding@resend.dev>"

    payload = {
        "from": from_email,
        "to": [recipient],
        "subject": subject,
        "html": html_content,
        "text": plain_text,
    }

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CareerForge-AI/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            resp_body = resp.read().decode("utf-8")
            logger.info(f"[RESEND SUCCESS] Email dispatched to {recipient}: {resp_body}")
            return True, "Email sent successfully via Resend."
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        logger.error(f"[RESEND HTTP ERROR] {err.code}: {raw}")
        try:
            err_json = json.loads(raw)
            clean_msg = err_json.get("message") or raw
        except Exception:
            clean_msg = raw
        return False, f"Resend ({err.code}): {clean_msg}"
    except Exception as exc:
        logger.error(f"[RESEND ERROR] {exc}")
        return False, f"Resend connection failed: {exc}"


def send_via_smtp(recipient: str, subject: str, html_content: str, plain_text: str) -> tuple[bool, str]:
    """
    Sends an email using standard SMTP (e.g. Gmail SMTP).
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((Config.SMTP_FROM_NAME, Config.SMTP_FROM_EMAIL))
    msg["To"] = recipient

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        if Config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=12)
        else:
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=12)
            if Config.SMTP_USE_TLS:
                server.starttls()

        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.sendmail(Config.SMTP_FROM_EMAIL, [recipient], msg.as_string())
        server.quit()
        logger.info(f"[SMTP SUCCESS] Verification code successfully sent to {recipient}")
        return True, "Email sent successfully via SMTP."
    except Exception as exc:
        logger.error(f"[SMTP ERROR] Failed to send email to {recipient}: {exc}")
        return False, str(exc)


def send_otp_email(to_email: str, otp_code: str) -> tuple[bool, str]:
    """
    Sends a 6-digit verification code using Resend (priority) or SMTP.
    If neither is configured, falls back to dev mode and logs the code.
    Returns: (success: bool, status_message: str)
    """
    recipient = to_email.strip().lower()
    clean_code = str(otp_code).strip()
    subject = f"{clean_code} is your CareerForge.AI Google verification code"
    plain_text, html_content = _build_otp_templates(clean_code)

    # 1. Primary: Resend API
    if is_resend_configured():
        logger.info(f"[EMAIL] Delivering via Resend API to {recipient}...")
        return send_via_resend(recipient, subject, html_content, plain_text)

    # 2. Secondary: SMTP Server
    if is_smtp_configured():
        logger.info(f"[EMAIL] Delivering via SMTP to {recipient}...")
        return send_via_smtp(recipient, subject, html_content, plain_text)

    # 3. Fallback: Safe dev mode
    logger.warning(
        f"[EMAIL DEV MODE] Neither Resend nor SMTP configured in .env. "
        f"Generated test PIN for '{recipient}' is: {clean_code}"
    )
    return True, "dev_mode"


def send_password_reset_email(to_email: str, otp_code: str) -> tuple[bool, str]:
    """Sends a 6-digit password reset PIN via Resend or SMTP."""
    recipient = to_email.strip().lower()
    clean_code = str(otp_code).strip()
    subject = f"{clean_code} is your CareerForge.AI Password Reset code"
    plain_text = f"""CareerForge.AI · Career Development Platform
Password Reset Request

Use the following 6-digit code to reset your password:

{clean_code}

This code expires in 30 minutes. If you did not request a password reset, you can safely ignore this email.

— The CareerForge.AI Team
"""
    html_content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Password Reset · CareerForge.AI</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0b0f19; color: #f1f5f9; margin: 0; padding: 32px 16px;">
  <div style="max-width: 520px; margin: 0 auto; background: #111827; border-radius: 16px; padding: 32px 28px; border: 1px solid rgba(255,255,255,0.08);">
    <div style="font-size: 22px; font-weight: 800; color: #ffffff; margin-bottom: 20px;">
      CareerForge.<span style="color: #6d5dfc;">AI</span>
    </div>
    <h1 style="font-size: 20px; font-weight: 700; margin: 0 0 12px; color: #f8fafc;">Reset Your Password</h1>
    <p style="font-size: 14px; line-height: 1.6; color: #94a3b8; margin: 0 0 24px;">You requested to reset your password on CareerForge.AI. Use the verification code below to set a new password:</p>
    <div style="background: rgba(109, 93, 252, 0.12); border: 1px solid rgba(109, 93, 252, 0.35); border-radius: 12px; padding: 18px 24px; text-align: center; margin: 20px 0;">
      <span style="font-family: monospace; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #a5b4fc;">{clean_code}</span>
    </div>
    <p style="font-size: 13px; color: #cbd5e1;">This code is valid for <strong>30 minutes</strong>. Do not share this code with anyone.</p>
    <p style="font-size: 12px; color: #64748b; margin-top: 16px;">If you did not initiate this request, you can safely ignore this email.</p>
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 12px; color: #64748b; text-align: center;">
      Sent by CareerForge.AI &bull; Career Development Platform
    </div>
  </div>
</body>
</html>"""
    if is_resend_configured():
        return send_via_resend(recipient, subject, html_content, plain_text)
    if is_smtp_configured():
        return send_via_smtp(recipient, subject, html_content, plain_text)
    return True, "dev_mode"


def send_github_otp_email(to_email: str, otp_code: str) -> tuple[bool, str]:
    """Sends a 6-digit GitHub verification PIN via Resend or SMTP."""
    recipient = to_email.strip().lower()
    clean_code = str(otp_code).strip()
    subject = f"{clean_code} is your CareerForge.AI GitHub verification code"
    plain_text = f"""CareerForge.AI · Career Development Platform
GitHub Sign-In Verification

Your 6-digit GitHub verification code is:

{clean_code}

This code expires in 30 minutes. If you did not request this sign-in, you can safely ignore this email.

— The CareerForge.AI Team
"""
    html_content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>GitHub Sign-In · CareerForge.AI</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0d1117; color: #c9d1d9; margin: 0; padding: 32px 16px;">
  <div style="max-width: 520px; margin: 0 auto; background: #161b22; border-radius: 16px; padding: 32px 28px; border: 1px solid #30363d;">
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="#f0f6fc">
        <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
      </svg>
      <span style="font-size: 20px; font-weight: 800; color: #ffffff;">CareerForge.<span style="color: #6d5dfc;">AI</span></span>
    </div>
    <h1 style="font-size: 20px; font-weight: 700; margin: 0 0 12px; color: #f0f6fc;">Verify Your GitHub Sign-In</h1>
    <p style="font-size: 14px; line-height: 1.6; color: #8b949e; margin: 0 0 24px;">Use the 6-digit code below to securely sign in to CareerForge.AI with your GitHub account:</p>
    <div style="background: rgba(35, 134, 54, 0.15); border: 1px solid rgba(46, 160, 67, 0.4); border-radius: 12px; padding: 18px 24px; text-align: center; margin: 20px 0;">
      <span style="font-family: monospace; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #7ee787;">{clean_code}</span>
    </div>
    <p style="font-size: 13px; color: #8b949e;">This code is valid for <strong>30 minutes</strong>. Do not share this code with anyone.</p>
    <p style="font-size: 12px; color: #484f58; margin-top: 16px;">If you did not initiate this request, you can safely ignore this email.</p>
    <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #30363d; font-size: 12px; color: #484f58; text-align: center;">
      Sent by CareerForge.AI &bull; Career Development Platform
    </div>
  </div>
</body>
</html>"""
    if is_resend_configured():
        return send_via_resend(recipient, subject, html_content, plain_text)
    if is_smtp_configured():
        return send_via_smtp(recipient, subject, html_content, plain_text)
    return True, "dev_mode"


