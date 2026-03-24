# ============================================================
# ARIA - Master Executor
# Sab modules ko connect karta hai — brain of ARIA
# ============================================================

import os
import sys
import time
import platform
from datetime import datetime
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint

# ARIA core modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.nlp_engine import NLPEngine
from core.voice_system import VoiceSystem
from core.memory_system import MemorySystem
from core.task_planner import TaskPlanner
from modules.file_manager import FileManager
from modules.app_controller import AppController
from modules.email_system import EmailSystem
from config.settings import (
    GEMINI_API_KEY, DB_PATH, CHROMA_PATH,
    GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH,
    SEARCH_PATHS, WHISPER_MODEL, SAMPLE_RATE,
    ARIA_VOICE_RATE, ARIA_VOICE_VOLUME,
    OUTPUTS_DIR
)

console = Console()


class MasterExecutor:
    """
    ARIA ka Master Executor — sab ka boss!
    NLP → Intent → Plan → Execute → Speak → Remember
    """

    VERSION = "1.0.0 Phase 1"

    def __init__(self):
        console.print(Panel.fit(
            "[bold cyan]🤖 ARIA[/bold cyan] — Initializing...",
            style="cyan"
        ))

        # Initialize all modules
        self.nlp = NLPEngine()
        self.voice = VoiceSystem({
            "WHISPER_MODEL": WHISPER_MODEL,
            "SAMPLE_RATE": SAMPLE_RATE,
            "ARIA_VOICE_RATE": ARIA_VOICE_RATE,
            "ARIA_VOICE_VOLUME": ARIA_VOICE_VOLUME,
        })
        self.memory = MemorySystem(db_path=DB_PATH)
        self.planner = TaskPlanner()
        self.file_manager = FileManager(search_paths=SEARCH_PATHS)
        self.app_controller = AppController()
        self.email_system = EmailSystem(
            gemini_api_key=GEMINI_API_KEY,
            credentials_path=GMAIL_CREDENTIALS_PATH,
            token_path=GMAIL_TOKEN_PATH,
        )

        self._running = False
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_email_draft = None

        logger.success("All modules initialized successfully!")

    def run(self, use_voice: bool = False):
        """
        ARIA main loop start karo.
        use_voice=True: Microphone se suno
        use_voice=False: Keyboard se type karo
        """
        self._running = True
        self._show_welcome()

        while self._running:
            try:
                # Input lo
                if use_voice:
                    user_input = self.voice.listen()
                else:
                    user_input = self._get_text_input()

                if not user_input or not user_input.strip():
                    continue

                # Process karo
                self._process_command(user_input)

            except KeyboardInterrupt:
                console.print("\n[yellow]Ctrl+C detected — ARIA band ho rahi hai...[/yellow]")
                self._shutdown()
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                self.voice.speak("Koi error aa gayi — dobara try karo")

    def _process_command(self, user_input: str):
        """
        User input process karo — full pipeline.
        Input → NLP → Plan → Execute → Memory → Speak
        """
        console.print(f"\n[bold white]👤 Aap:[/bold white] {user_input}")

        # Step 1: Intent detect karo
        intent_result = self.nlp.detect_intent(user_input)
        intent = intent_result["intent"]
        entities = intent_result["entities"]
        confidence = intent_result["confidence"]

        console.print(f"[dim]Intent: {intent} ({confidence:.0%})[/dim]")

        # Step 2: Plan banao
        steps = self.planner.plan(intent_result)

        # Step 3: Execute karo
        response = self._execute_steps(steps, entities, user_input)

        # Step 4: Memory mein save karo
        self.memory.save_conversation(
            user_input=user_input,
            aria_response=response,
            intent=intent,
            session_id=self._session_id
        )

    def _execute_steps(self, steps: list, entities: dict,
                       original_input: str) -> str:
        """Steps ko execute karo."""
        last_response = ""

        for step in steps:
            action = step.get("action")
            step_entities = step.get("entities", entities)

            try:
                result = self._execute_action(
                    action, step, step_entities, original_input
                )
                if result:
                    last_response = str(result)

            except Exception as e:
                logger.error(f"Step execution error [{action}]: {e}")
                self.voice.speak(f"Ek step mein error aa gayi: {action}")

        return last_response

    def _execute_action(self, action: str, step: dict,
                        entities: dict, original_input: str):
        """Single action execute karo."""

        # ── SPEAK ───────────────────────────────────────────
        if action == "speak":
            text = step.get("text", "")
            self.voice.speak(text)
            return text

        elif action == "speak_result":
            return None  # Handled separately after result

        # ── SCREENSHOT ──────────────────────────────────────
        elif action == "take_screenshot":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(OUTPUTS_DIR / "screenshots" / f"screenshot_{timestamp}.png")
            path = self.app_controller.take_screenshot(save_path)
            if path and not path.startswith("Error"):
                self.voice.speak(f"Screenshot le liya! Desktop pe save ho gaya.")
                console.print(f"[green]✅ Screenshot:[/green] {path}")
            else:
                self.voice.speak("Screenshot lene mein masla ho gaya")
            return path

        # ── SYSTEM STATUS ────────────────────────────────────
        elif action == "get_system_status":
            status = self.app_controller.get_system_status()
            self._display_system_status(status)
            return status

        elif action == "show_status":
            return None  # Already displayed in get_system_status

        # ── APP OPEN ────────────────────────────────────────
        elif action == "open_application":
            app_name = entities.get("app_name", "")
            if not app_name:
                # Try to extract from original input
                app_name = self._extract_app_from_text(original_input)

            if app_name:
                result = self.app_controller.open_app(app_name)
                if result["success"]:
                    self.voice.speak(result["message"])
                else:
                    self.voice.speak(result["message"])
            else:
                self.voice.speak("Kaunsa app kholna hai? Naam batao please.")
            return app_name

        # ── APP CLOSE ────────────────────────────────────────
        elif action == "close_application":
            app_name = entities.get("app_name", "")
            if not app_name:
                app_name = self._extract_app_from_text(original_input)

            if app_name:
                result = self.app_controller.close_app(app_name)
                self.voice.speak(result["message"])
            return app_name

        # ── FILE SEARCH ─────────────────────────────────────
        elif action == "search_files":
            filename = entities.get("filename", "")
            file_type = self._extract_file_type(original_input)

            if not filename and not file_type:
                # Generic search — first meaningful word use karo
                words = original_input.lower().split()
                stop_words = {"meri", "mera", "ki", "ka", "ko", "dhoondo",
                              "find", "search", "file", "files", "karo"}
                for word in words:
                    if word not in stop_words and len(word) > 2:
                        filename = word
                        break

            results = self.file_manager.search_files(
                query=filename or "",
                file_type=file_type
            )
            self._display_file_results(results)
            self.voice.speak(f"{len(results)} files mili hain!")
            return results

        # ── FILE ORGANIZE ────────────────────────────────────
        elif action == "preview_organize":
            folder = entities.get("folder", "Downloads")
            folder_path = str(Path.home() / folder.capitalize())
            preview = self.file_manager.organize_folder(
                folder_path=folder_path, dry_run=True
            )
            count = preview.get("files_organized", 0)
            self.voice.speak(f"{count} files hain organize karne ke liye.")
            return preview

        elif action == "organize_files":
            folder = entities.get("folder", "Downloads")
            folder_path = str(Path.home() / folder.capitalize())

            console.print(f"\n[yellow]Organize karo: {folder}?[/yellow]")
            confirm = input("Han/No (h/n): ").lower().strip()

            if confirm in ['h', 'han', 'yes', 'y', 'haan']:
                result = self.file_manager.organize_folder(folder_path=folder_path)
                count = result.get("files_organized", 0)
                self.voice.speak(f"Ho gaya! {count} files organize ho gayi!")
                console.print(f"[green]✅ {count} files organized[/green]")
            else:
                self.voice.speak("Theek hai, chhod deta hun")
            return folder

        # ── EMAIL DRAFT ─────────────────────────────────────
        elif action == "draft_email":
            recipient = entities.get("recipient", "")
            if not recipient:
                recipient = self._extract_person_from_text(original_input)

            if not recipient:
                self.voice.speak("Kisko email likhna hai? Naam batao.")
                recipient = input("Recipient ka naam: ").strip()

            # Context extract karo
            context = original_input

            draft = self.email_system.draft_email(
                recipient_name=recipient,
                context=context,
            )

            if draft["success"]:
                self._display_email_draft(draft)
                self._current_email_draft = draft
                self.voice.speak(f"{recipient} ke liye email draft ho gaya. Dekhein screen pe.")
            else:
                self.voice.speak(draft.get("message", "Email draft nahi ho saka"))

            return draft

        elif action == "show_email_draft":
            return None  # Already displayed in draft_email

        # ── EMAIL SEND ──────────────────────────────────────
        elif action == "send_email":
            if not self._current_email_draft:
                self.voice.speak("Pehle email draft karo phir send karun")
                return

            draft = self._current_email_draft
            to_email = input(f"Email address ({draft['recipient']}): ").strip()

            if "@" not in to_email:
                self.voice.speak("Valid email address chahiye")
                return

            result = self.email_system.send_email(
                to_email=to_email,
                subject=draft["subject"],
                body=draft["body"],
            )

            if result["success"]:
                self.memory.log_email(
                    recipient=to_email,
                    subject=draft["subject"],
                    body_preview=draft["body"][:200],
                    gmail_message_id=result.get("message_id"),
                )
                self.voice.speak(f"Email bhej diya {draft['recipient']} ko!")
                self._current_email_draft = None
            else:
                self.voice.speak(result.get("message", "Email send nahi hua"))
            return result

        # ── CONFIRM ─────────────────────────────────────────
        elif action == "confirm":
            message = step.get("message", "Kya confirm karna hai?")
            console.print(f"\n[yellow]⚠️  {message}[/yellow]")
            answer = input("Han/No (h/n): ").lower().strip()
            return answer in ['h', 'han', 'yes', 'y', 'haan']

        # ── HELP ────────────────────────────────────────────
        elif action == "show_help":
            self._show_help()
            return "help shown"

        elif action == "show_capabilities":
            self._show_capabilities()
            return "capabilities shown"

        # ── TIME/DATE ────────────────────────────────────────
        elif action == "get_time_date":
            now = datetime.now()
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%d %B %Y, %A")
            self.voice.speak(f"Abhi {time_str} baj rahe hain. Aaj {date_str} hai.")
            console.print(f"[cyan]🕐 {time_str} | 📅 {date_str}[/cyan]")
            return f"{time_str} | {date_str}"

        # ── SHUTDOWN ────────────────────────────────────────
        elif action == "shutdown":
            self._shutdown()
            return "shutdown"

        # ── ASK CLARIFICATION ────────────────────────────────
        elif action == "ask_clarification":
            console.print("[yellow]Available commands:[/yellow] screenshot, files dhoondo, chrome kholo, system status, email likho, help")
            return None

        return None

    # ── HELPERS ───────────────────────────────────────────────

    def _extract_app_from_text(self, text: str) -> str:
        """Text se app name extract karo."""
        apps = ["chrome", "firefox", "notepad", "excel", "word",
                "vlc", "spotify", "vscode", "calculator", "paint",
                "explorer", "powershell", "cmd"]
        text_lower = text.lower()
        for app in apps:
            if app in text_lower:
                return app
        return ""

    def _extract_file_type(self, text: str) -> str:
        """Text se file type extract karo."""
        text_lower = text.lower()
        type_map = {
            "pdf": "pdf", "image": "image", "photo": "image",
            "video": "video", "document": "document", "excel": "spreadsheet",
            "word": "document", "music": "audio", "audio": "audio",
        }
        for keyword, ftype in type_map.items():
            if keyword in text_lower:
                return ftype
        return ""

    def _extract_person_from_text(self, text: str) -> str:
        """Text se person name extract karo."""
        import re
        # "ahmed ko email", "sara ko likho" patterns
        patterns = [
            r'(\w+)\s+(?:ko|ke liye|for)\s+(?:email|mail|message)',
            r'(?:dear|to)\s+(\w+)',
            r'email\s+(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).capitalize()
                if len(name) > 2 and name.lower() not in {'ko', 'ke', 'ka'}:
                    return name
        return ""

    def _display_system_status(self, status: dict):
        """System status beautifully display karo."""
        if "error" in status:
            console.print(f"[red]Status error: {status['error']}[/red]")
            return

        table = Table(title="💻 System Status", style="cyan")
        table.add_column("Component", style="bold")
        table.add_column("Status", style="green")
        table.add_column("Details")

        cpu = status.get("cpu", {})
        ram = status.get("ram", {})
        disk = status.get("disk", {})
        battery = status.get("battery")

        table.add_row("CPU", cpu.get("usage", "N/A"),
                      f"{cpu.get('cores', '?')} cores")
        table.add_row("RAM", ram.get("percent", "N/A"),
                      f"{ram.get('used', '?')} / {ram.get('total', '?')}")
        table.add_row("Disk C:", disk.get("percent", "N/A"),
                      f"{disk.get('free', '?')} free")

        if battery:
            bat_status = "🔌 " if battery.get("plugged") else "🔋 "
            table.add_row("Battery",
                          f"{bat_status}{battery.get('percent', '?')}%",
                          battery.get("status", ""))

        console.print(table)

        # Voice response
        cpu_usage = cpu.get('usage', 'N/A')
        ram_usage = ram.get('percent', 'N/A')
        self.voice.speak(
            f"CPU {cpu_usage} use ho raha hai. RAM {ram_usage} use ho rahi hai."
        )

    def _display_file_results(self, results: list):
        """File results display karo."""
        if not results:
            console.print("[yellow]Koi file nahi mili[/yellow]")
            return

        table = Table(title=f"📁 Files Found ({len(results)})", style="blue")
        table.add_column("#", style="dim", width=4)
        table.add_column("File Name", style="bold")
        table.add_column("Size")
        table.add_column("Modified")
        table.add_column("Location", style="dim")

        for i, f in enumerate(results[:15], 1):
            path = Path(f["path"])
            table.add_row(
                str(i),
                f["name"],
                f["size"],
                f["modified"],
                str(path.parent)[:50],
            )

        console.print(table)

    def _display_email_draft(self, draft: dict):
        """Email draft display karo."""
        console.print(Panel(
            f"[bold]To:[/bold] {draft.get('recipient', '')}\n"
            f"[bold]Subject:[/bold] {draft.get('subject', '')}\n\n"
            f"{draft.get('body', '')}",
            title="📧 Email Draft",
            style="green"
        ))

    def _show_welcome(self):
        """Welcome screen dikhao."""
        welcome_text = Text()
        welcome_text.append("🤖 ARIA", style="bold cyan")
        welcome_text.append(" — Automated Responsive Intelligent Assistant\n", style="white")
        welcome_text.append(f"Version: {self.VERSION}\n", style="dim")
        welcome_text.append("Urdu • English • Roman Urdu\n", style="yellow")

        console.print(Panel(welcome_text, style="cyan"))

        stats = self.memory.get_stats()
        console.print(
            f"[dim]Conversations: {stats['total_conversations']} | "
            f"Contacts: {stats['total_contacts']} | "
            f"Emails: {stats['emails_sent']}[/dim]\n"
        )

        self.voice.speak(
            "Salam! Main ARIA hun. Kya kar sakta hun aapke liye? "
            "Help ke liye 'help' likhein."
        )

    def _show_help(self):
        """Help display karo."""
        table = Table(title="📋 ARIA Commands — Phase 1", style="green")
        table.add_column("Command", style="bold yellow")
        table.add_column("ARIA Kya Karta Hai")

        commands = [
            ("hello aria", "Greet karta hai"),
            ("screenshot lo", "Screen capture — Desktop pe save"),
            ("meri pdf files dhoondo", "PDFs search karta hai"),
            ("chrome kholo", "Chrome browser open"),
            ("system status batao", "CPU, RAM, Battery, Disk info"),
            ("ahmed ko email likho", "AI se professional email draft"),
            ("Downloads organize karo", "Files type ke hisaab se sort"),
            ("duplicate files dhoondo", "Same files dhoondta hai"),
            ("help", "Yeh help screen"),
            ("band ho jao / stop", "ARIA band karo"),
        ]

        for cmd, desc in commands:
            table.add_row(f'"{cmd}"', desc)

        console.print(table)

    def _show_capabilities(self):
        """Capabilities dikhao (short version)."""
        console.print(
            "[cyan]📋 Main kya kar sakta hun:[/cyan]\n"
            "  • Screenshot lena\n"
            "  • Files dhoondna\n"
            "  • Apps kholna/band karna\n"
            "  • System status check karna\n"
            "  • Email draft karna (AI se)\n"
            "  • Folders organize karna\n"
            "  • Duplicate files dhoondna\n\n"
            "[dim]'help' likhein poori list ke liye[/dim]"
        )

    def _shutdown(self):
        """ARIA gracefully band karo."""
        self._running = False
        console.print("[yellow]\n👋 ARIA band ho rahi hai — Khuda Hafiz![/yellow]")
        logger.info("ARIA shutdown complete")


# ── MAIN ENTRY POINT ─────────────────────────────────────────

def main():
    """ARIA start karo."""
    import argparse

    parser = argparse.ArgumentParser(description="ARIA — AI Personal Assistant")
    parser.add_argument(
        "--voice", "-v",
        action="store_true",
        help="Voice mode (microphone se suno)"
    )
    parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Text mode (keyboard se type karo) [default]"
    )
    args = parser.parse_args()

    use_voice = args.voice and not args.text

    aria = MasterExecutor()
    aria.run(use_voice=use_voice)


if __name__ == "__main__":
    main()
