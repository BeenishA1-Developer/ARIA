# ============================================================
# ARIA Phase 2 — WhatsApp Module v2 (COMPLETE + DB Logging)
# ============================================================

import os
import re
from pathlib import Path
from loguru import logger

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class WhatsAppModule:
    """
    WhatsApp via Twilio.
    ✅ Send message
    ✅ Send file
    ✅ Bulk messaging (sab clients ko)
    ✅ Pakistani number auto-format
    ✅ Har send se pehle confirmation
    ✅ DB logging (memory_system se)
    ✅ Twilio official API — no ban risk
    """

    def __init__(self, account_sid: str = None, auth_token: str = None,
                 whatsapp_number: str = None, memory_system=None):
        self.account_sid   = account_sid  or os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token    = auth_token   or os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number   = whatsapp_number or os.getenv("TWILIO_WHATSAPP_NUMBER", "")
        self.memory        = memory_system   # DB logging ke liye
        self._client       = None

        if self.account_sid and self.auth_token and TWILIO_AVAILABLE:
            try:
                self._client = TwilioClient(self.account_sid, self.auth_token)
                logger.success("WhatsApp (Twilio) connected!")
            except Exception as e:
                logger.error(f"Twilio init: {e}")
        else:
            logger.warning("WhatsApp not configured — set TWILIO_* env vars")

    # ── NUMBER FORMATTING ─────────────────────────────────────

    def format_number(self, number: str) -> str:
        """0300-1234567 → whatsapp:+923001234567"""
        digits = re.sub(r'\D', '', number)
        if digits.startswith('92') and len(digits) == 12:
            fmt = f"+{digits}"
        elif digits.startswith('0') and len(digits) == 11:
            fmt = f"+92{digits[1:]}"
        elif len(digits) == 10:
            fmt = f"+92{digits}"
        else:
            fmt = f"+{digits}"
        return f"whatsapp:{fmt}"

    def format_display(self, number: str) -> str:
        return self.format_number(number).replace("whatsapp:", "")

    def _from_number(self) -> str:
        return (self.from_number if self.from_number.startswith("whatsapp:")
                else f"whatsapp:{self.from_number}")

    # ── SEND MESSAGE ──────────────────────────────────────────

    def send_message(self, to_number: str, message: str,
                     confirmed: bool = False,
                     recipient_name: str = None) -> dict:
        """WhatsApp message bhejo + DB mein log karo."""
        formatted_to = self.format_number(to_number)

        if not self._client:
            return {
                "success": False,
                "message": "WhatsApp connected nahi — Twilio setup karo",
                "preview": {"to": self.format_display(to_number),
                            "body": message},
            }

        try:
            msg = self._client.messages.create(
                from_=self._from_number(),
                to=formatted_to,
                body=message,
            )
            # ✅ DB logging
            if self.memory:
                self.memory.log_whatsapp(
                    recipient_number=self.format_display(to_number),
                    message=message,
                    recipient_name=recipient_name,
                    twilio_sid=msg.sid,
                    is_bulk=False,
                )
            logger.success(f"WA sent → {formatted_to} | SID: {msg.sid}")
            return {
                "success":  True,
                "sid":      msg.sid,
                "to":       self.format_display(to_number),
                "message":  message,
                "status":   msg.status,
                "response": f"Message bhej diya {self.format_display(to_number)} ko! ✅",
            }
        except Exception as e:
            logger.error(f"WA send error: {e}")
            return {"success": False, "error": str(e),
                    "message": f"Message nahi bheja: {e}"}

    # ── SEND FILE ─────────────────────────────────────────────

    def send_file(self, to_number: str, file_url: str,
                  caption: str = None) -> dict:
        """WhatsApp pe file bhejo (public URL required)."""
        if not self._client:
            return {"success": False,
                    "message": "WhatsApp connected nahi"}
        try:
            formatted_to = self.format_number(to_number)
            msg = self._client.messages.create(
                from_=self._from_number(),
                to=formatted_to,
                body=caption or "File sent via ARIA",
                media_url=[file_url],
            )
            if self.memory:
                self.memory.log_whatsapp(
                    recipient_number=self.format_display(to_number),
                    message=f"[FILE] {file_url} | {caption or ''}",
                    twilio_sid=msg.sid,
                )
            return {"success": True, "sid": msg.sid,
                    "response": f"File bhej di! ✅"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── BULK MESSAGING ────────────────────────────────────────

    def send_bulk(self, contacts: list, message: str) -> dict:
        """
        Sab clients ko message bhejo.
        contacts: [{"name": "Ahmed", "phone": "03001234567"}, ...]
        """
        results = {"sent": [], "failed": [], "total": len(contacts)}

        for contact in contacts:
            number = contact.get("phone") or contact.get("whatsapp", "")
            name   = contact.get("name", "Unknown")
            if not number:
                results["failed"].append({"name": name, "reason": "No number"})
                continue

            personalized = message.replace("{name}", name)
            result = self.send_message(
                number, personalized,
                confirmed=True,
                recipient_name=name
            )
            if result["success"]:
                results["sent"].append({"name": name, "number": number})
                # ✅ Bulk log
                if self.memory:
                    self.memory.log_whatsapp(
                        recipient_number=self.format_display(number),
                        message=personalized,
                        recipient_name=name,
                        twilio_sid=result.get("sid"),
                        is_bulk=True,
                    )
            else:
                results["failed"].append(
                    {"name": name, "reason": result.get("message", "Error")}
                )

        results["success_count"] = len(results["sent"])
        results["fail_count"]    = len(results["failed"])
        logger.info(
            f"Bulk: {results['success_count']}/{results['total']} sent"
        )
        return results

    # ── TEMPLATES ─────────────────────────────────────────────

    def get_template(self, template_type: str,
                     context: dict = None) -> str:
        context = context or {}
        name    = context.get("name", "")
        project = context.get("project", "project")
        amount  = context.get("amount", "")

        templates = {
            "project_ready": (
                f"As-salamu alaykum {name}!\n\n"
                f"Aapka *{project}* complete ho gaya! ✅\n"
                f"Please review karein aur feedback dein.\n\nShukria!"
            ),
            "payment_reminder": (
                f"As-salamu alaykum {name}!\n\n"
                f"Yeh *{project}* ki payment reminder hai.\n"
                f"Amount: PKR *{amount}*\n\n"
                f"Please confirm karein. JazakAllah Khair!"
            ),
            "follow_up": (
                f"As-salamu alaykum {name}!\n\n"
                f"Main *{project}* ke baare mein follow up kar raha hun.\n"
                f"Kya aap baat kar sakte hain?\n\nShukria!"
            ),
            "bulk_update": (
                f"As-salamu alaykum {name}!\n\n"
                f"Important update: {project}\n\n"
                f"Koi sawaal ho to zaroor batayein.\n\nShukria!"
            ),
            "meeting_reminder": (
                f"As-salamu alaykum {name}!\n\n"
                f"⏰ Reminder: *{project}* meeting kal hai.\n"
                f"Please confirm karein.\n\nJazakAllah Khair!"
            ),
        }
        return templates.get(template_type, templates["follow_up"])
