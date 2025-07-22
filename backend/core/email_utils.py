# If you see 'Import "jinja2" could not be resolved', run: pip install jinja2
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape

template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_template(template_name: str = "", **context):
    if not template_name or not isinstance(template_name, str):
        raise ValueError("template_name must be a non-empty string")
    template = template_env.get_template(template_name)
    return template.render(**context)


def send_email(to: str, subject: str, body: str, html_body: str = None):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not smtp_user or not smtp_password:
        raise RuntimeError(
            "SMTP_USER and SMTP_PASSWORD must be set in environment variables."
        )
    from_email = smtp_user

    msg = MIMEMultipart("alternative")
    msg["From"] = str(from_email)
    msg["To"] = str(to)
    msg["Subject"] = str(subject)
    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(str(smtp_user), str(smtp_password))
        server.sendmail(str(from_email), str(to), msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")
