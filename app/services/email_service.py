import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings
from app.utils.email_templates import EmailTemplates
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.smtp_enabled = settings.SMTP_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email asynchronously"""

        if not self.smtp_enabled:
            logger.info(f"SMTP disabled. Would send email to {to_email}: {subject}")
            return True

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to_email,
            subject,
            html_content,
            text_content,
        )

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email synchronously"""

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)

            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_verification_email(
        self, to_email: str, username: str, verification_link: str
    ) -> bool:
        """Send email verification"""

        subject = f"Verify your email - {settings.APP_NAME}"
        html_content = EmailTemplates.get_verification_template(
            username=username,
            verification_link=verification_link,
            app_name=settings.APP_NAME,
        )

        return await self.send_email(to_email, subject, html_content)

    async def send_password_reset_email(
        self, to_email: str, username: str, reset_link: str
    ) -> bool:
        """Send password reset email"""

        subject = f"Reset your password - {settings.APP_NAME}"
        html_content = EmailTemplates.get_password_reset_template(
            username=username, reset_link=reset_link, app_name=settings.APP_NAME
        )

        return await self.send_email(to_email, subject, html_content)

    async def send_welcome_email(
        self, to_email: str, username: str, company_name: Optional[str] = None
    ) -> bool:
        """Send welcome email"""

        subject = f"Welcome to {settings.APP_NAME}!"
        html_content = EmailTemplates.get_welcome_template(
            username=username, company_name=company_name, app_name=settings.APP_NAME
        )

        return await self.send_email(to_email, subject, html_content)
