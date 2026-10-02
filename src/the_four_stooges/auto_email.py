# send_email.py
import os, sys, smtplib, ssl
from email.message import EmailMessage
import re

SENDER = "4stoogescs2026@gmail.com"                           # your Gmail address
APP_PASSWORD = "lqbxvbrkaihkhheh"    # Gmail App Password

def send_email(to: str, body: str, subject: str = "Message"):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(SENDER, APP_PASSWORD)
        s.send_message(msg)

def is_valid_email(address: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
    return re.match(pattern, address.strip()) is not None

if __name__ == "__main__":
    recipient = SENDER   # sending to yourself
    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    send_email(recipient, text)
    print(f"Sent to {recipient}")