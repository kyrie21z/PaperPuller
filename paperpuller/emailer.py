from __future__ import annotations

from datetime import date
from email.header import Header
from email.mime.text import MIMEText
import html
import os
import smtplib

from .config import AppConfig


def render_email_html(report_date: date, rows: list[dict]) -> str:
    items = []
    for row in rows:
        items.append(
            f"""
            <li>
              <h3>{html.escape(row['title'])}</h3>
              <p><strong>Score:</strong> {row['score']:.1f} | <strong>Tags:</strong> {html.escape(', '.join(row['topic_tags']))}</p>
              <p>{html.escape(row['tldr'])}</p>
              <p><strong>Reason:</strong> {html.escape(row['reason'])}</p>
              <p><a href="{html.escape(row['abs_url'])}">arXiv</a> | <a href="{html.escape(row['pdf_url'])}">PDF</a></p>
            </li>
            """.strip()
        )
    body = "\n".join(items) if items else "<p>No relevant papers today.</p>"
    return f"""
<!doctype html>
<html>
  <body>
    <h1>Daily arXiv Papers - {report_date.isoformat()}</h1>
    <ol>
      {body}
    </ol>
  </body>
</html>
""".strip()


def send_email(config: AppConfig, report_date: date, rows: list[dict]) -> None:
    password = os.environ.get(config.email.password_env)
    if not password:
        raise RuntimeError(f"Missing SMTP password environment variable: {config.email.password_env}")
    password = password.strip()
    if "gmail.com" in config.email.smtp_server.lower():
        password = password.replace(" ", "")

    receivers = [value.strip() for value in config.email.receiver.split(",") if value.strip()]
    if not receivers:
        raise RuntimeError("No email receiver configured")

    message = MIMEText(render_email_html(report_date, rows), "html", "utf-8")
    message["From"] = config.email.sender
    message["To"] = ", ".join(receivers)
    message["Subject"] = Header(f"{config.email.subject} {report_date.isoformat()}", "utf-8").encode()

    if config.email.smtp_port == 465:
        server = smtplib.SMTP_SSL(config.email.smtp_server, config.email.smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(config.email.smtp_server, config.email.smtp_port, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()
    try:
        server.login(config.email.sender, password)
        server.sendmail(config.email.sender, receivers, message.as_string())
    finally:
        server.quit()
