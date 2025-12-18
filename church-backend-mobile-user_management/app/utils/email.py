import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import BackgroundTasks

from ..config import settings
from ..schemas.auth import EmailNotification


def send_email(background_tasks: BackgroundTasks, notification: EmailNotification) -> None:
    """Send email notification via SMTP."""

    def _deliver():
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = settings.from_email
            msg["To"] = notification.recipient
            msg["Subject"] = notification.subject

            # Add body to email
            msg.attach(MIMEText(notification.message, "plain"))

            # Create SMTP session
            server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
            server.starttls()  # Enable security
            server.login(settings.smtp_username, settings.smtp_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(settings.from_email, notification.recipient, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {notification.recipient}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Error: {e}")
            print("⚠️  Gmail requires App Password if 2FA is enabled.")
            print("   Steps to fix:")
            print("   1. Enable 2FA on your Google account")
            print("   2. Go to: https://myaccount.google.com/apppasswords")
            print("   3. Generate an App Password for 'Mail'")
            print("   4. Use that App Password in your .env file (SMTP_PASSWORD)")
            print(f"\n[EMAIL FALLBACK - OTP CODE IN CONSOLE]")
            print(f"To: {notification.recipient}")
            print(f"Subject: {notification.subject}")
            # Extract OTP code from message if present
            if 'OTP code is: ' in notification.message:
                newline = '\n'
                otp_code = notification.message.split('OTP code is: ')[1].split(newline)[0]
                print(f"⚠️  OTP CODE: {otp_code}")
            else:
                print("OTP Code: See full message below")
            print(f"Full Message:\n{notification.message}")
        except Exception as e:
            print(f"❌ Error sending email to {notification.recipient}: {e}")
            print(f"\n[EMAIL FALLBACK - OTP CODE IN CONSOLE]")
            print(f"To: {notification.recipient}")
            print(f"Subject: {notification.subject}")
            # Extract OTP code from message if present
            if 'OTP code is: ' in notification.message:
                otp_code = notification.message.split('OTP code is: ')[1].split('\n')[0]
                print(f"⚠️  OTP CODE: {otp_code}")
            print(f"Full Message:\n{notification.message}")

    background_tasks.add_task(_deliver)
