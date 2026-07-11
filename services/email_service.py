import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import CONFIG
import logging

logger = logging.getLogger(__name__)

def send_email(subject, body):
    sender_email = CONFIG['SENDER_EMAIL']
    receiver_email = CONFIG.get('RECEIVER_EMAIL', sender_email)
    password = CONFIG['SENDER_PASSWORD']

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    content_type = "html" if "<html" in body.lower() or "<table" in body.lower() else "plain"
    part = MIMEText(body, content_type)
    message.attach(part)

    try:
        server = smtplib.SMTP(CONFIG['SMTP_SERVER'], CONFIG['SMTP_PORT'])
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
