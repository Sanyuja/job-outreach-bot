# src/gmail_draft.py

import os
import base64
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from .gmail_client import get_gmail_service


def create_draft_with_resume(
    to_email: str,
    subject: str,
    html_body: str,
    resume_path: str,
):
    """
    Create a Gmail draft with:
    - given recipient
    - subject
    - HTML body
    - attached resume file
    """

    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"Resume file not found at: {resume_path}")

    # Build MIME message
    message = MIMEMultipart()
    message["to"] = to_email
    message["subject"] = subject

    # Attach HTML body
    message.attach(MIMEText(html_body, "html"))

    # Attach resume
    mime_type, _ = mimetypes.guess_type(resume_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    main_type, sub_type = mime_type.split("/", 1)

    with open(resume_path, "rb") as f:
        part = MIMEBase(main_type, sub_type)
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{os.path.basename(resume_path)}"',
        )
        message.attach(part)

    # Encode for Gmail API
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft_body = {"message": {"raw": raw}}

    service = get_gmail_service()
    draft = (
        service.users()
        .drafts()
        .create(userId="me", body=draft_body)
        .execute()
    )

    print(f"[GMAIL] Draft created with id: {draft.get('id')}")
    return draft
