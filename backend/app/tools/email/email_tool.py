from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.config.settings import settings
from app.tools.base.tool_interface import BaseTool, ToolResult


class EmailTool(BaseTool):
    name = "email"
    description = "Send email notifications via SMTP"
    category = "communication"
    required_permissions = ["read:own_data"]
    risk_score = 0.1

    def __init__(self) -> None:
        super().__init__()

    async def execute(self, **kwargs: Any) -> ToolResult:
        action = kwargs.get("action", "send_email")
        if action == "send_email":
            to = kwargs.get("to", [])
            subject = kwargs.get("subject", "")
            body = kwargs.get("body", "")
            html = kwargs.get("html", False)
            try:
                msg = MIMEMultipart("alternative")
                msg["From"] = settings.smtp_from
                msg["To"] = ", ".join(to) if isinstance(to, list) else to
                msg["Subject"] = subject
                content_type = "html" if html else "plain"
                msg.attach(MIMEText(body, content_type))
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_username, settings.smtp_password)
                    server.sendmail(
                        settings.smtp_from, to if isinstance(to, list) else [to], msg.as_string()
                    )
                return ToolResult(success=True, data={"message": "Email sent successfully"})
            except Exception as e:
                return ToolResult(success=False, error=str(e))
        return ToolResult(success=False, error=f"Unknown action: {action}")

    async def validate_params(self, **kwargs: Any) -> bool:
        return kwargs.get("action") == "send_email" and "to" in kwargs and "subject" in kwargs

    async def health_check(self) -> bool:
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as server:
                server.starttls()
                return True
        except Exception:
            return False
