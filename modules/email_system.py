# ============================================================
# ARIA - Email System
# Gmail API se email draft + send karna
# ============================================================

import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    logger.warning("Gmail libraries not installed — email features limited")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class EmailSystem:
    """
    ARIA ka Email System.
    - Gemini AI se professional email draft karta hai
    - Gmail API se directly send karta hai
    - Contacts se email dhoondta hai
    - Inbox check karta hai
    """

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/contacts.readonly',
    ]

    def __init__(self, gemini_api_key: str = None,
                 credentials_path: str = "config/gmail_credentials.json",
                 token_path: str = "data/gmail_token.json"):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._gmail_service = None
        self._ai_model = None

        self._init_ai()
        logger.info("Email System initialized")

    def _init_ai(self):
        """Gemini AI initialize karo."""
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self._ai_model = genai.GenerativeModel("gemini-1.5-flash")
                logger.success("Gemini AI ready for email drafting")
            except Exception as e:
                logger.error(f"Gemini init failed: {e}")

    def _get_gmail_service(self):
        """Gmail API service lo (OAuth2)."""
        if not GMAIL_AVAILABLE:
            return None

        if self._gmail_service:
            return self._gmail_service

        creds = None
        token_path = Path(self.token_path)
        creds_path = Path(self.credentials_path)

        # Saved token check karo
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(token_path), self.SCOPES
                )
            except Exception:
                pass

        # Token refresh ya new auth
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                if not creds_path.exists():
                    logger.warning(f"Gmail credentials nahi mili: {creds_path}")
                    return None

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(creds_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Token save karo
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'w') as f:
                f.write(creds.to_json())

        self._gmail_service = build('gmail', 'v1', credentials=creds)
        logger.success("Gmail service connected!")
        return self._gmail_service

    # ── EMAIL DRAFT ───────────────────────────────────────────

    def draft_email(self, recipient_name: str, subject: str = None,
                    context: str = None, tone: str = "professional",
                    language: str = "english") -> dict:
        """
        AI se professional email draft karo.
        recipient_name: "Ahmed", "Manager", "Client" etc.
        context: Email kis baare mein hai
        tone: "professional", "friendly", "formal"
        language: "english", "urdu"
        """
        if not self._ai_model:
            return {
                "success": False,
                "message": "Gemini API key nahi hai — email draft nahi ho sakta",
                "subject": subject or "Meeting Request",
                "body": f"Dear {recipient_name},\n\nI hope this email finds you well.\n\nBest regards"
            }

        # Prompt banao
        prompt = f"""
You are a professional email writer. Write a professional email in {language}.

Recipient: {recipient_name}
Context/Purpose: {context or 'General professional communication'}
Tone: {tone}
Subject: {subject or 'Generate an appropriate subject'}

Write ONLY the email content with:
1. Subject line (format: "Subject: ...")
2. Greeting
3. Body (2-3 paragraphs)
4. Professional closing
5. Signature placeholder: [Your Name]

Keep it concise, professional, and appropriate.
Do NOT add any extra commentary — just the email.
"""
        try:
            response = self._ai_model.generate_content(prompt)
            email_text = response.text.strip()

            # Subject extract karo
            subject_line = subject
            body = email_text

            if "Subject:" in email_text:
                lines = email_text.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("Subject:"):
                        subject_line = line.replace("Subject:", "").strip()
                        body = '\n'.join(lines[i+1:]).strip()
                        break

            logger.success(f"Email drafted for: {recipient_name}")
            return {
                "success": True,
                "recipient": recipient_name,
                "subject": subject_line or "Professional Communication",
                "body": body,
                "tone": tone,
            }

        except Exception as e:
            logger.error(f"Email draft error: {e}")
            return {
                "success": False,
                "message": f"Email draft nahi ho saka: {e}",
            }

    # ── EMAIL SEND ────────────────────────────────────────────

    def send_email(self, to_email: str, subject: str,
                   body: str, cc: str = None) -> dict:
        """
        Gmail se email send karo.
        Pehle confirm karo — phir send karo.
        """
        service = self._get_gmail_service()
        if not service:
            return {
                "success": False,
                "message": "Gmail connected nahi hai — pehle setup karo"
            }

        try:
            # Email message banao
            msg = MIMEMultipart('alternative')
            msg['To'] = to_email
            msg['Subject'] = subject
            if cc:
                msg['Cc'] = cc

            # Plain text + HTML
            text_part = MIMEText(body, 'plain', 'utf-8')
            html_body = body.replace('\n', '<br>')
            html_part = MIMEText(
                f"<html><body><p>{html_body}</p></body></html>",
                'html', 'utf-8'
            )
            msg.attach(text_part)
            msg.attach(html_part)

            # Base64 encode
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

            # Send via Gmail API
            result = service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            message_id = result.get('id')
            logger.success(f"Email sent! ID: {message_id} → {to_email}")

            return {
                "success": True,
                "message_id": message_id,
                "to": to_email,
                "subject": subject,
                "message": f"Email successfully bhej diya: {to_email}",
            }

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {
                "success": False,
                "message": f"Email send nahi ho saka: {e}",
            }

    # ── INBOX CHECK ───────────────────────────────────────────

    def check_inbox(self, max_results: int = 10) -> list:
        """
        Gmail inbox check karo — last emails.
        """
        service = self._get_gmail_service()
        if not service:
            return []

        try:
            result = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()

            messages = result.get('messages', [])
            emails = []

            for msg_ref in messages[:max_results]:
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_ref['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value']
                           for h in msg['payload']['headers']}
                snippet = msg.get('snippet', '')

                emails.append({
                    "id": msg_ref['id'],
                    "from": headers.get('From', 'Unknown'),
                    "subject": headers.get('Subject', '(No Subject)'),
                    "date": headers.get('Date', ''),
                    "preview": snippet[:100] + "..." if len(snippet) > 100 else snippet,
                    "unread": 'UNREAD' in msg.get('labelIds', []),
                })

            logger.info(f"Inbox fetched: {len(emails)} emails")
            return emails

        except Exception as e:
            logger.error(f"Inbox check error: {e}")
            return []

    # ── EMAIL TEMPLATES ───────────────────────────────────────

    def get_email_template(self, template_type: str,
                           context: dict = None) -> dict:
        """
        Ready-made email templates.
        template_type: 'follow_up', 'invoice', 'project_update',
                       'thank_you', 'introduction'
        """
        context = context or {}
        name = context.get('name', 'Client')
        amount = context.get('amount', '')
        project = context.get('project', 'Project')

        templates = {
            "follow_up": {
                "subject": f"Follow-up: {project}",
                "body": f"""Dear {name},

I hope you are doing well. I wanted to follow up on our previous conversation regarding {project}.

Could you please let me know the current status? I am available for a call or meeting at your convenience.

Looking forward to your response.

Best regards,
[Your Name]"""
            },
            "invoice": {
                "subject": f"Invoice for {project} Services",
                "body": f"""Dear {name},

Please find below the invoice details for services rendered:

Project: {project}
Amount: {amount}
Due Date: 30 days from today

Payment can be made via bank transfer or other agreed method.

Please do not hesitate to contact me if you have any questions.

Thank you for your business.

Best regards,
[Your Name]"""
            },
            "project_update": {
                "subject": f"Project Update: {project}",
                "body": f"""Dear {name},

I wanted to provide you with a quick update on {project}.

Current Status: In Progress
Completion: On track as per schedule

I will continue to keep you updated on any significant developments.

Best regards,
[Your Name]"""
            },
            "thank_you": {
                "subject": "Thank You",
                "body": f"""Dear {name},

Thank you very much for your time and consideration.

I truly appreciate the opportunity and look forward to working with you.

Best regards,
[Your Name]"""
            },
        }

        template = templates.get(template_type, templates["follow_up"])
        return {
            "success": True,
            "template_type": template_type,
            **template
        }
