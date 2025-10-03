from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from typing import List
import logging
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
            VALIDATE_CERTS=True
        )
        self.fastmail = FastMail(self.config)
    
    async def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True):
        """Send email using FastMail."""
        try:
            # Create message
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=body,
                subtype=MessageType.html if is_html else MessageType.plain
            )
            
            # Send email
            await self.fastmail.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_verification_email(self, to_email: str, verification_token: str, base_url: str):
        """Send email verification email."""
        verification_url = f"{base_url}/api/auth/verify-email?token={verification_token}"
        
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
    
    async def send_password_reset_email(self, to_email: str, reset_token: str, base_url: str):
        """Send password reset email."""
        reset_url = f"{base_url}/reset-password?token={reset_token}"
        
        subject = "Скидання паролю"
        
        body = f"""
        <html>
            <head></head>
            <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #333;">Скидання паролю</h2>
                    <p>Ви запросили скидання паролю для вашого акаунту.</p>
                    <p>Натисніть на кнопку нижче, щоб встановити новий пароль:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #dc3545; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Скинути пароль
                        </a>
                    </div>
                    
                    <p>Або скопіюйте та вставте це посилання у ваш браузер:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    
                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        Якщо ви не запитували скидання паролю, просто проігноруйте цей лист.
                        Посилання дійсне протягом 1 години.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, is_html=True)

# Create global instance
email_service = EmailService()