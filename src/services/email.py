from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import List
import logging
import os
from pathlib import Path
from src.conf.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending verification and notification emails using fastapi_mail."""

    def __init__(self):
        # Configure email connection
        self.config = ConnectionConfig(
            MAIL_USERNAME=settings.smtp_username,
            MAIL_PASSWORD=settings.smtp_password,
            MAIL_FROM=settings.from_email,
            MAIL_PORT=settings.smtp_port,
            MAIL_SERVER=settings.smtp_server,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        self.fastmail = FastMail(self.config)

    async def send_email(
        self, to_email: str, subject: str, body: str, is_html: bool = True
    ):
        """Send email using FastMail."""
        try:
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=body,
                subtype=MessageType.html if is_html else MessageType.plain,
            )

            # Send email
            await self.fastmail.send_message(message)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    async def send_verification_email(
        self, to_email: str, verification_token: str, base_url: str
    ):
        """Send email verification email."""
        verification_url = (
            f"{base_url}/api/auth/verify-email?token={verification_token}"
        )

        subject = "Підтвердіть вашу електронну адресу"

        body = f"""
        <html>
            <head></head>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Підтвердження електронної адреси</h2>
                    <p>Вітаємо!</p>
                    <p>Дякуємо за реєстрацію. Будь ласка, підтвердіть вашу електронну адресу, натиснувши на кнопку нижче:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #007bff; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Підтвердити електронну адресу
                        </a>
                    </div>
                    
                    <p>Або скопіюйте та вставте це посилання у ваш браузер:</p>
                    <p><a href="{verification_url}">{verification_url}</a></p>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        Якщо ви не реєструвалися на нашому сайті, просто проігноруйте цей лист.
                    </p>
                </div>
            </body>
        </html>
        """

        return await self.send_email(to_email, subject, body, is_html=True)

    async def send_password_reset_email(
        self, to_email: str, username: str, reset_token: str, base_url: str
    ):
        """Send password reset email using HTML template.

        Args:
            to_email (str): Recipient email address
            username (str): User's username for personalization
            reset_token (str): Password reset token
            base_url (str): Base URL for reset link

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create reset URL for frontend/API
            reset_url = f"{base_url}/api/auth/reset-password?token={reset_token}"

            # Load HTML template
            template_path = (
                Path(__file__).parent.parent.parent
                / "templates"
                / "password_reset_email.html"
            )

            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    html_template = f.read()

                # Replace template variables
                body = html_template.replace("{{ username }}", username)
                body = body.replace("{{ email }}", to_email)
                body = body.replace("{{ reset_token }}", reset_token)
                body = body.replace("{{ reset_link }}", reset_url)

            else:
                # Fallback simple HTML if template not found
                logger.warning(
                    f"Template not found at {template_path}, using fallback HTML"
                )
                body = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>🔒 Password Reset Request</h2>
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>We received a request to reset your password for {to_email}.</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">
                            Reset My Password
                        </a>
                    </div>
                    <p><strong>Reset Token:</strong> {reset_token}</p>
                    <p style="color: #856404; background: #fff3cd; padding: 15px; border-radius: 5px;">
                        ⚠️ This link expires in 1 hour. If you didn't request this, please ignore this email.
                    </p>
                </div>
                """

            subject = "🔒 Password Reset Request - Contacts API"
            return await self.send_email(to_email, subject, body, is_html=True)

        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False


# Create global instance
email_service = EmailService()
