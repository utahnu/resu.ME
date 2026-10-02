from backend import ai_slop
from auto_email import send_email, is_valid_email

try:
    import markdown as md
except ImportError:
    md = None


def send_newsletter(email):
    email = email.strip()
    if not is_valid_email(email):
        raise ValueError("Please enter a valid email address.")

    newsletter = ai_slop("No resume provided. Write a general newsletter for job-hunting students.", [])
    send_email(
    to=email,
    body=newsletter,
    subject="The 4 Stooges Slop",
)


if __name__ == "__main__":
    import sys
    send_newsletter(sys.argv[1])
    print("Email sent!")