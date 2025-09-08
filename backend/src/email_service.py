"""
Email service for sending password reset and notification emails
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending transactional emails"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.EMAIL_ENABLED:
            logger.warning("Email service is disabled. Enable it by setting EMAIL_ENABLED=true")
            return False
            
        if not all([settings.SMTP_HOST, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
            logger.error("Email configuration incomplete. Please set SMTP_HOST, SMTP_USERNAME, and SMTP_PASSWORD")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            
        Returns:
            True if email sent successfully, False otherwise
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = "Reset Your StreamAPI Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>StreamAPI</h1>
                    <p>Password Reset Request</p>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <center>
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </center>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #fff; padding: 10px; border-radius: 5px;">
                        {reset_url}
                    </p>
                    
                    <p><strong>This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours.</strong></p>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© 2024 StreamAPI. All rights reserved.</p>
                    <p>This is an automated email. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        StreamAPI Password Reset
        
        Hello!
        
        We received a request to reset your password. Visit the link below to create a new password:
        
        {reset_url}
        
        This link will expire in {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        © 2024 StreamAPI. All rights reserved.
        """
        
        return EmailService.send_email(to_email, subject, html_content, text_content)
    
    @staticmethod
    def send_welcome_email(to_email: str, username: str) -> bool:
        """
        Send welcome email to new users
        
        Args:
            to_email: Recipient email address
            username: User's username
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Welcome to StreamAPI!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .feature {{
                    padding: 10px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to StreamAPI!</h1>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for joining StreamAPI. We're excited to help you streamline your API development workflow.</p>
                    
                    <h3>Here's what you can do with StreamAPI:</h3>
                    <div class="feature">✅ <strong>API Discovery</strong> - Automatically discover and document APIs in your codebase</div>
                    <div class="feature">✅ <strong>Mock Servers</strong> - Generate instant mock servers from OpenAPI specs</div>
                    <div class="feature">✅ <strong>AI Analysis</strong> - Get security and performance insights</div>
                    <div class="feature">✅ <strong>Test Generation</strong> - Auto-generate comprehensive API tests</div>
                    <div class="feature">✅ <strong>Export/Import</strong> - Export to OpenAPI, Postman, and more</div>
                    
                    <center>
                        <a href="{settings.FRONTEND_URL}/dashboard" class="button">Go to Dashboard</a>
                    </center>
                    
                    <p>Need help? Check out our documentation or contact support.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to StreamAPI!
        
        Hello {username}!
        
        Thank you for joining StreamAPI. We're excited to help you streamline your API development workflow.
        
        Here's what you can do with StreamAPI:
        - API Discovery - Automatically discover and document APIs in your codebase
        - Mock Servers - Generate instant mock servers from OpenAPI specs
        - AI Analysis - Get security and performance insights
        - Test Generation - Auto-generate comprehensive API tests
        - Export/Import - Export to OpenAPI, Postman, and more
        
        Visit your dashboard: {settings.FRONTEND_URL}/dashboard
        
        Need help? Check out our documentation or contact support.
        """
        
        return EmailService.send_email(to_email, subject, html_content, text_content)

# Export the service
email_service = EmailService()

# Additional functions for workspace invitations
async def send_invitation_email(
    email: str,
    workspace_name: str,
    inviter_name: str,
    token: str,
    message: Optional[str] = None
) -> bool:
    """Send workspace invitation email"""
    invite_url = f"{settings.FRONTEND_URL}/invite/{token}"
    
    subject = f"You're invited to join {workspace_name} on StreamAPI"
    
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>You're invited to join {workspace_name}!</h2>
        <p>{inviter_name} has invited you to collaborate on StreamAPI.</p>
        {f'<p>{message}</p>' if message else ''}
        <a href="{invite_url}" style="display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 5px;">Accept Invitation</a>
        <p>This invitation expires in 7 days.</p>
    </div>
    """
    
    return email_service.send_email(email, subject, html_content)

async def send_notification_email(
    email: str,
    subject: str,
    body: str
) -> bool:
    """Send general notification email"""
    return email_service.send_email(email, subject, f"<div>{body}</div>", body)