"""Fetch the latest monitor draft from Gmail and auto-send it.

Reads Gmail drafts via IMAP, finds the most recent draft with subject starting
with one of the configured prefixes (e.g. '[LITE]'), sends it via SMTP to
the user's own inbox, then deletes the draft to avoid buildup.

Environment variables:
    GMAIL_USERNAME         Gmail address (e.g. user@gmail.com)
    GMAIL_APP_PASSWORD     16-char App Password (spaces allowed)
    SUBJECT_PREFIXES       Comma-separated subject prefixes to match.
                           Default: '[LITE],🟠 [LITE],🔴 [LITE]'

Exit codes:
    0  success or no matching draft (not an error)
    1  auth / connection failure
"""

from __future__ import annotations

import email
import imaplib
import os
import smtplib
import sys
from email.header import decode_header, make_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
DRAFTS_MAILBOX = '"[Gmail]/Drafts"'


def decode_subject(raw: str) -> str:
    try:
        return str(make_header(decode_header(raw or "")))
    except Exception:
        return raw or ""


def extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")


def find_and_delete_latest_draft(
    imap: imaplib.IMAP4_SSL, prefixes: list[str]
) -> tuple[str, str] | tuple[None, None]:
    status, _ = imap.select(DRAFTS_MAILBOX)
    if status != "OK":
        print(f"Cannot open drafts mailbox: {status}", file=sys.stderr)
        return None, None

    status, data = imap.search(None, "ALL")
    if status != "OK" or not data or not data[0]:
        return None, None

    ids = data[0].split()
    for mid in reversed(ids[-50:]):
        status, msg_data = imap.fetch(mid, "(RFC822)")
        if status != "OK" or not msg_data or not msg_data[0]:
            continue
        raw = msg_data[0][1]
        if not isinstance(raw, (bytes, bytearray)):
            continue
        msg = email.message_from_bytes(raw)
        subject = decode_subject(msg.get("Subject", ""))
        if not any(subject.startswith(p) for p in prefixes):
            continue

        body = extract_body(msg)
        imap.store(mid, "+FLAGS", "\\Deleted")
        imap.expunge()
        return subject, body

    return None, None


def send(to_addr: str, from_addr: str, subject: str, body: str, password: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.login(from_addr, password)
        smtp.send_message(msg)


def main() -> int:
    user = os.environ.get("GMAIL_USERNAME")
    password = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    prefixes = [
        p.strip()
        for p in os.environ.get("SUBJECT_PREFIXES", "[LITE],🟠 [LITE],🔴 [LITE]").split(",")
        if p.strip()
    ]

    if not user or not password:
        print("GMAIL_USERNAME / GMAIL_APP_PASSWORD not set", file=sys.stderr)
        return 1

    try:
        with imaplib.IMAP4_SSL(IMAP_HOST) as imap:
            imap.login(user, password)
            subject, body = find_and_delete_latest_draft(imap, prefixes)
    except imaplib.IMAP4.error as exc:
        print(f"IMAP auth/connection failed: {exc}", file=sys.stderr)
        return 1

    if not subject:
        print("No matching draft found. Exiting quietly.")
        return 0

    print(f"Sending draft: {subject}")
    send(to_addr=user, from_addr=user, subject=subject, body=body, password=password)
    print("Sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
