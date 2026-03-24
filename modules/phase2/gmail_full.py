# ============================================================
# ARIA Phase 2 — Gmail Full Automation
# Send, Read, Reply, Search, Templates, Auto-Reminders
# ============================================================

import os
import base64
import json
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from loguru import logger

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GmailFull:
    """
    ARIA Phase 2 — Gmail Full Automation.
    - Email directly send (sirf draft nahi)
    - Inbox check — last N emails summary
    - Email reply AI se suggest karta hai
    - Template memory: project update, invoice, follow-up
    - Name/keyword se email search
    - Client follow-up auto-reminder (1 week baad)
    """

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/contacts.readonly',
    ]

    def __init__(self, gemini_api_key: str = None,
                 credentials_path: str = "config/gmail_credentials.json",
                 token_path: str = "data/gmail_token.json"):
        self.gemini_api_key    = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.credentials_path  = credentials_path
        self.token_path        = token_path
        self._service          = None
        self._ai               = None
        self._init_ai()
        logger.info("Gmail Full module initialized")

    def _init_ai(self):
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self._ai = genai.GenerativeModel("gemini-1.5-flash")
                logger.success("Gemini AI ready")
            except Exception as e:
                logger.error(f"Gemini init: {e}")

    def _get_service(self):
        if self._service:
            return self._service
        if not GMAIL_AVAILABLE:
            return None

        creds = None
        token_path = Path(self.token_path)
        creds_path = Path(self.credentials_path)

        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(token_path), self.SCOPES
                )
            except Exception:
                pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                if not creds_path.exists():
                    logger.warning("Gmail credentials file nahi mili")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'w') as f:
                f.write(creds.to_json())

        self._service = build('gmail', 'v1', credentials=creds)
        logger.success("Gmail connected!")
        return self._service

    # ── SEND EMAIL ────────────────────────────────────────────

    def send_email(self, to_email: str, subject: str,
                   body: str, attachment_path: str = None,
                   cc: str = None) -> dict:
        """Gmail se email seedha send karo."""
        service = self._get_service()
        if not service:
            return {"success": False,
                    "message": "Gmail connected nahi — credentials setup karo"}

        try:
            msg = MIMEMultipart()
            msg['To']      = to_email
            msg['Subject'] = subject
            if cc:
                msg['Cc'] = cc

            # Body
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Attachment
            if attachment_path:
                path = Path(attachment_path)
                if path.exists():
                    with open(path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{path.name}"'
                    )
                    msg.attach(part)
                    logger.info(f"Attachment added: {path.name}")

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            result = service.users().messages().send(
                userId='me', body={'raw': raw}
            ).execute()

            logger.success(f"Email sent → {to_email}")
            return {
                "success": True,
                "message_id": result.get('id'),
                "to": to_email,
                "subject": subject,
                "response": f"Email bhej diya {to_email} ko! ✅",
            }

        except Exception as e:
            logger.error(f"Send email error: {e}")
            return {"success": False, "message": str(e)}

    # ── CHECK INBOX ───────────────────────────────────────────

    def check_inbox(self, max_results: int = 10,
                    unread_only: bool = False) -> list:
        """Inbox check karo — emails ki summary."""
        service = self._get_service()
        if not service:
            return []

        try:
            label_ids = ['INBOX']
            if unread_only:
                label_ids.append('UNREAD')

            result = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=label_ids,
            ).execute()

            emails = []
            for m in result.get('messages', []):
                msg = service.users().messages().get(
                    userId='me', id=m['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers  = {h['name']: h['value']
                            for h in msg['payload']['headers']}
                snippet  = msg.get('snippet', '')
                is_unread = 'UNREAD' in msg.get('labelIds', [])

                emails.append({
                    "id":       m['id'],
                    "from":     headers.get('From', 'Unknown'),
                    "subject":  headers.get('Subject', '(No Subject)'),
                    "date":     headers.get('Date', ''),
                    "preview":  snippet[:120],
                    "unread":   is_unread,
                })

            logger.info(f"Inbox: {len(emails)} emails fetched")
            return emails

        except Exception as e:
            logger.error(f"Inbox error: {e}")
            return []

    # ── READ FULL EMAIL ───────────────────────────────────────

    def read_email(self, message_id: str) -> dict:
        """Specific email poori padho."""
        service = self._get_service()
        if not service:
            return {}

        try:
            msg = service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()

            headers = {h['name']: h['value']
                       for h in msg['payload']['headers']}

            # Body extract karo
            body = self._extract_body(msg['payload'])

            # Mark as read
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            return {
                "id":      message_id,
                "from":    headers.get('From', ''),
                "to":      headers.get('To', ''),
                "subject": headers.get('Subject', ''),
                "date":    headers.get('Date', ''),
                "body":    body,
            }

        except Exception as e:
            logger.error(f"Read email error: {e}")
            return {}

    def _extract_body(self, payload: dict) -> str:
        """Email body extract karo."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8', errors='replace')

        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode(
                            'utf-8', errors='replace'
                        )
        return ""

    # ── AI REPLY ─────────────────────────────────────────────

    def suggest_reply(self, email_content: dict,
                      reply_hint: str = None) -> dict:
        """AI se email reply suggest karo."""
        if not self._ai:
            return {
                "success": False,
                "message": "Gemini API key set nahi hai",
            }

        prompt = f"""
You are a professional email assistant. Write a professional reply to this email.

Original Email:
From: {email_content.get('from', '')}
Subject: {email_content.get('subject', '')}
Body: {email_content.get('body', '')[:500]}

Reply guidance: {reply_hint or 'Write a helpful, professional reply'}

Write ONLY the reply body (no subject line needed).
Keep it concise and professional.
End with: Best regards, [Your Name]
"""
        try:
            resp = self._ai.generate_content(prompt)
            return {
                "success": True,
                "reply": resp.text.strip(),
                "subject": f"Re: {email_content.get('subject', '')}",
                "to": email_content.get('from', ''),
            }
        except Exception as e:
            logger.error(f"AI reply error: {e}")
            return {"success": False, "message": str(e)}

    # ── SEARCH EMAILS ─────────────────────────────────────────

    def search_emails(self, query: str,
                      max_results: int = 10) -> list:
        """
        Emails search karo — name ya keyword se.
        "Ahmed ki email dhoondo" → from:ahmed
        """
        service = self._get_service()
        if not service:
            return []

        try:
            result = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
            ).execute()

            emails = []
            for m in result.get('messages', []):
                msg = service.users().messages().get(
                    userId='me', id=m['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                headers = {h['name']: h['value']
                           for h in msg['payload']['headers']}
                emails.append({
                    "id":      m['id'],
                    "from":    headers.get('From', ''),
                    "subject": headers.get('Subject', ''),
                    "date":    headers.get('Date', ''),
                    "preview": msg.get('snippet', '')[:100],
                })

            logger.info(f"Search '{query}': {len(emails)} found")
            return emails

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    # ── FOLLOW-UP REMINDER ────────────────────────────────────

    def schedule_followup(self, recipient: str, subject: str,
                          days: int = 7) -> dict:
        """
        Follow-up reminder schedule karo.
        N din baad automatically follow-up email.
        """
        followup_date = datetime.now() + timedelta(days=days)

        # Database mein save karo (TaskScheduler use karega)
        task = {
            "type":         "email_followup",
            "recipient":    recipient,
            "subject":      f"Follow-up: {subject}",
            "scheduled_at": followup_date.isoformat(),
            "days":         days,
            "created_at":   datetime.now().isoformat(),
        }

        logger.info(f"Follow-up scheduled: {recipient} on {followup_date.date()}")
        return {
            "success":      True,
            "recipient":    recipient,
            "follow_up_on": followup_date.strftime("%d %B %Y"),
            "message":      f"Follow-up {days} din baad: {followup_date.strftime('%d %B %Y')}",
            "task":         task,
        }

    # ── EMAIL TEMPLATES ───────────────────────────────────────

    def get_template(self, template_type: str,
                     context: dict = None) -> dict:
        """Professional email templates."""
        context = context or {}
        name    = context.get('name', 'Client')
        project = context.get('project', 'the project')
        amount  = context.get('amount', '')
        date    = context.get('date', '')

        templates = {
            "project_update": {
                "subject": f"Project Update — {project}",
                "body": (
                    f"Dear {name},\n\nI hope you are doing well.\n\n"
                    f"I wanted to provide you with an update on {project}.\n\n"
                    f"Current Status: Work is progressing as planned.\n"
                    f"Expected Completion: On schedule.\n\n"
                    f"I will keep you informed of any developments.\n\n"
                    f"Best regards,\n[Your Name]"
                ),
            },
            "invoice": {
                "subject": f"Invoice — {project}",
                "body": (
                    f"Dear {name},\n\nThank you for your business.\n\n"
                    f"Please find the invoice details:\n"
                    f"Project: {project}\nAmount: PKR {amount}\n"
                    f"Due Date: {date or '30 days from today'}\n\n"
                    f"Kindly process the payment at your earliest convenience.\n\n"
                    f"Best regards,\n[Your Name]"
                ),
            },
            "follow_up": {
                "subject": f"Follow-up — {project}",
                "body": (
                    f"Dear {name},\n\nI hope all is well.\n\n"
                    f"I am following up regarding {project}.\n"
                    f"Could you please share an update on the current status?\n\n"
                    f"I am available for a call at your convenience.\n\n"
                    f"Best regards,\n[Your Name]"
                ),
            },
            "thank_you": {
                "subject": "Thank You",
                "body": (
                    f"Dear {name},\n\nThank you very much for your time "
                    f"and consideration.\n\n"
                    f"I truly appreciate the opportunity and look forward "
                    f"to working with you.\n\n"
                    f"Best regards,\n[Your Name]"
                ),
            },
            "introduction": {
                "subject": "Introduction — Freelance Services",
                "body": (
                    f"Dear {name},\n\nI hope this email finds you well.\n\n"
                    f"I am reaching out to introduce my freelance services "
                    f"in {project}.\n\n"
                    f"I have extensive experience and would love to discuss "
                    f"how I can help your projects.\n\n"
                    f"Looking forward to connecting.\n\n"
                    f"Best regards,\n[Your Name]"
                ),
            },
        }

        tpl = templates.get(template_type, templates["follow_up"])
        return {"success": True, "template_type": template_type, **tpl}
