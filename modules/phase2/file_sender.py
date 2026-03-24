# ============================================================
# ARIA Phase 2 — File Auto-Send System v2
# ============================================================

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from loguru import logger


class FileSender:
    """
    ARIA Phase 2 — File Auto-Send.
    ✅ File email bhejo (auto-search + attach)
    ✅ Folder zip + email
    ✅ File WhatsApp pe bhejo
    ✅ File copy
    ✅ Sent log
    """

    def __init__(self, email_system=None, whatsapp_module=None,
                 memory_system=None):
        self.email    = email_system
        self.whatsapp = whatsapp_module
        self.memory   = memory_system
        self.temp_dir = Path("outputs/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info("File Sender initialized")

    def _search_file(self, query: str):
        """File dhoondo."""
        from modules.file_manager import FileManager
        fm = FileManager()
        return fm.search_files(query)

    # ── SEND FILE VIA EMAIL ───────────────────────────────────

    def send_file_email(self, file_query: str, recipient_email: str,
                        recipient_name: str = None,
                        message: str = None) -> dict:
        """File dhoondo aur email se bhejo."""
        if not self.email:
            return {"success": False,
                    "message": "Email system connected nahi — pehle setup karo"}

        results = self._search_file(file_query)
        if not results:
            return {"success": False,
                    "message": f"File nahi mili: '{file_query}'"}

        file_path = results[0]["path"]
        file_name = results[0]["name"]
        name      = recipient_name or "Sir/Madam"
        body      = message or (
            f"Dear {name},\n\n"
            f"Please find the attached file: {file_name}\n\n"
            f"Best regards"
        )

        result = self.email.send_email(
            to_email=recipient_email,
            subject=f"File: {file_name}",
            body=body,
            attachment_path=file_path,
        )

        if result["success"] and self.memory:
            self.memory.log_file_operation(
                "email_send", file_path, recipient_email, True
            )
            self.memory.log_email(
                recipient_email,
                f"File: {file_name}",
                body[:200]
            )
        return result

    # ── ZIP FOLDER AND SEND ───────────────────────────────────

    def zip_and_send_email(self, folder_path: str,
                           recipient_email: str,
                           subject: str = None) -> dict:
        """Folder zip karke email se bhejo."""
        if not self.email:
            return {"success": False,
                    "message": "Email system connected nahi",
                    "zip_path": None}

        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return {"success": False,
                    "message": f"Folder nahi mila: {folder_path}"}

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = f"{folder.name}_{ts}.zip"
        zip_path = self.temp_dir / zip_name

        try:
            with zipfile.ZipFile(zip_path, 'w',
                                 zipfile.ZIP_DEFLATED) as zf:
                for fp in folder.rglob("*"):
                    if fp.is_file():
                        zf.write(fp, fp.relative_to(folder.parent))
            logger.success(f"Zipped: {zip_path}")
        except Exception as e:
            return {"success": False,
                    "message": f"Zip create nahi ho saka: {e}"}

        email_subject = subject or f"Project Files: {folder.name}"
        result = self.email.send_email(
            to_email=recipient_email,
            subject=email_subject,
            body=f"Please find attached: {folder.name}",
            attachment_path=str(zip_path),
        )

        # Cleanup
        try:
            zip_path.unlink()
        except Exception:
            pass

        return result

    # ── SEND FILE VIA WHATSAPP ────────────────────────────────

    def send_file_whatsapp(self, file_query: str,
                           phone_number: str,
                           caption: str = None) -> dict:
        """File info WhatsApp pe bhejo (URL nahi — message bhejta hai)."""
        if not self.whatsapp:
            return {"success": False,
                    "message": "WhatsApp module connected nahi"}

        results = self._search_file(file_query)
        if not results:
            return {"success": False,
                    "message": f"File nahi mili: '{file_query}'"}

        file_name = results[0]["name"]
        file_path = results[0]["path"]
        file_size = results[0]["size"]

        msg = caption or (
            f"File: *{file_name}*\n"
            f"Size: {file_size}\n"
            f"Location: {Path(file_path).parent}\n\n"
            f"Sent via ARIA ✅"
        )

        result = self.whatsapp.send_message(
            to_number=phone_number,
            message=msg,
            confirmed=True,
        )

        if result["success"] and self.memory:
            self.memory.log_file_operation(
                "whatsapp_notify", file_path, phone_number, True
            )
        return result

    # ── COPY FILE ─────────────────────────────────────────────

    def copy_file(self, file_query: str,
                  destination: str) -> dict:
        """File copy karo ek jagah se doosri jagah."""
        results = self._search_file(file_query)
        if not results:
            return {"success": False,
                    "message": f"File nahi mili: '{file_query}'"}

        src  = Path(results[0]["path"])
        dest = Path(destination)
        if dest.is_dir():
            dest = dest / src.name

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest))
            logger.success(f"Copied: {src.name} → {dest}")
            if self.memory:
                self.memory.log_file_operation(
                    "copy", str(src), str(dest), True
                )
            return {
                "success":     True,
                "source":      str(src),
                "destination": str(dest),
                "message":     f"File copy ho gaya: {src.name}",
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── SENT LOG ──────────────────────────────────────────────

    def get_sent_log(self, limit: int = 20) -> list:
        """Sent files ka log lo."""
        if self.memory:
            return self.memory.get_email_history(limit)
        return []
