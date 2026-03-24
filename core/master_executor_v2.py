# ============================================================
# ARIA — Master Executor v2 FINAL (Phase 1 + Phase 2 COMPLETE)
# All 13 gaps fixed. All roadmap features implemented.
# ============================================================

import os
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nlp_engine      import NLPEngine, _patch_phase2_intents
from core.voice_system    import VoiceSystem
from core.memory_system   import MemorySystem
from core.task_planner    import TaskPlanner
from modules.file_manager  import FileManager
from modules.app_controller import AppController
from modules.email_system   import EmailSystem
from modules.phase2.whatsapp_module import WhatsAppModule
from modules.phase2.gmail_full      import GmailFull
from modules.phase2.fiverr_engine   import FiverrEngine
from modules.phase2.task_scheduler  import TaskScheduler
from modules.phase2.file_sender     import FileSender

from config.settings import (
    GEMINI_API_KEY, DB_PATH, CHROMA_PATH,
    GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH,
    SEARCH_PATHS, WHISPER_MODEL, SAMPLE_RATE,
    ARIA_VOICE_RATE, ARIA_VOICE_VOLUME, OUTPUTS_DIR
)

console = Console()


class ARIAv2:
    """
    ARIA v2 FINAL — Phase 1 + Phase 2 COMPLETE.
    All roadmap features ✅
    """

    VERSION = "2.0 FINAL"

    def __init__(self):
        console.print(Panel.fit(
            "[bold cyan]🤖 ARIA v2 FINAL[/bold cyan] — Loading all modules...",
            style="cyan"
        ))

        self.memory = MemorySystem(db_path=DB_PATH, chroma_path=CHROMA_PATH)
        self.nlp    = NLPEngine()   # v2 — 55+ intents built-in
        self.voice  = VoiceSystem({
            "WHISPER_MODEL":   WHISPER_MODEL,
            "SAMPLE_RATE":     SAMPLE_RATE,
            "ARIA_VOICE_RATE": ARIA_VOICE_RATE,
            "ARIA_VOICE_VOLUME": ARIA_VOICE_VOLUME,
        })
        self.planner = TaskPlanner()
        self.files   = FileManager(search_paths=SEARCH_PATHS)
        self.apps    = AppController()
        self.email_p1 = EmailSystem(
            gemini_api_key=GEMINI_API_KEY,
            credentials_path=GMAIL_CREDENTIALS_PATH,
            token_path=GMAIL_TOKEN_PATH,
        )

        # Phase 2
        self.whatsapp  = WhatsAppModule(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            whatsapp_number=os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
            memory_system=self.memory,   # ✅ DB logging
        )
        self.gmail     = GmailFull(
            gemini_api_key=GEMINI_API_KEY,
            credentials_path=GMAIL_CREDENTIALS_PATH,
            token_path=GMAIL_TOKEN_PATH,
        )
        self.fiverr    = FiverrEngine(gemini_api_key=GEMINI_API_KEY)
        self.scheduler = TaskScheduler(tasks_file="data/scheduled_tasks.json")
        self.sender    = FileSender(
            email_system=self.gmail,
            whatsapp_module=self.whatsapp,
            memory_system=self.memory,
        )

        self._running       = False
        self._session_id    = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_draft = None

        # Background scheduler
        self.scheduler.start_background(executors={
            "email":    lambda d: self.gmail.send_email(**d),
            "whatsapp": lambda d: self.whatsapp.send_message(**d),
            "fiverr_report": lambda d: self.fiverr.generate_report(),
        })

        logger.success("ARIA v2 FINAL — ALL MODULES READY ✅")

    # ═══════════════════════════════════════════════════════════
    # MAIN LOOP
    # ═══════════════════════════════════════════════════════════

    def run(self, use_voice: bool = False):
        self._running = True
        self._show_welcome()
        while self._running:
            try:
                user_input = (self.voice.listen() if use_voice
                              else self._text_input())
                if not user_input or not user_input.strip():
                    continue
                self._process(user_input)
            except KeyboardInterrupt:
                console.print("\n[yellow]Shutting down...[/yellow]")
                self._shutdown()
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")
                self.voice.speak("Error aa gayi — dobara try karein")

    def _text_input(self) -> str:
        try:    return input("\n💬 Command: ").strip()
        except: return "stop"

    def _process(self, user_input: str):
        console.print(f"\n[bold white]👤 Aap:[/bold white] {user_input}")
        result   = self.nlp.detect_intent(user_input)
        intent   = result["intent"]
        entities = result["entities"]
        console.print(
            f"[dim]🎯 {intent} ({result['confidence']:.0%})[/dim]"
        )
        response = self._route(intent, entities, user_input)
        self.memory.save_conversation(
            user_input, response or "", intent, self._session_id
        )

    # ═══════════════════════════════════════════════════════════
    # ROUTER
    # ═══════════════════════════════════════════════════════════

    def _route(self, intent: str, entities: dict, raw: str) -> str:

        # ── Phase 1 ───────────────────────────────────────────
        if   intent == "greeting":            return self._greeting()
        elif intent == "screenshot":          return self._screenshot()
        elif intent == "screenshot_scheduled":return self._screenshot_scheduled(raw)
        elif intent == "diagnostics":         return self._diagnostics()
        elif intent == "system_status":       return self._system_status()
        elif intent == "app_open":            return self._app_open(entities, raw)
        elif intent == "app_close":           return self._app_close(entities, raw)
        elif intent == "file_search":         return self._file_search(entities, raw)
        elif intent == "file_organize":       return self._file_organize(entities, raw)
        elif intent == "find_duplicates":     return self._find_duplicates(entities, raw)
        elif intent == "pdf_merge":           return self._pdf_merge()
        elif intent == "file_create":         return self._file_create(raw)
        elif intent == "email_draft":         return self._email_draft(entities, raw)
        elif intent == "volume_control":      return self._volume(raw)
        elif intent == "time_date":           return self._time()

        # ── Phase 2 ───────────────────────────────────────────
        elif intent == "whatsapp_send":
            # If filename detected — route to file_send instead
            if entities.get("filename") or any(
                w in raw.lower() for w in [".pdf",".docx",".jpg",".png","cv ","resume "]
            ):
                return self._file_send(entities, raw)
            return self._whatsapp_send(entities, raw)
        elif intent == "whatsapp_bulk":       return self._whatsapp_bulk(raw)
        elif intent == "email_send_now":      return self._email_send(entities, raw)
        elif intent == "inbox_check":         return self._inbox_check()
        elif intent == "email_reply":         return self._email_reply()
        elif intent == "email_search":        return self._email_search(raw)
        elif intent == "file_send":           return self._file_send(entities, raw)
        elif intent == "folder_send":         return self._folder_send(raw)
        elif intent == "fiverr_keywords":     return self._fiverr_keywords(entities, raw)
        elif intent == "fiverr_keyword_frequency": return self._fiverr_freq()
        elif intent == "fiverr_ranking":      return self._fiverr_ranking(entities, raw)
        elif intent == "fiverr_title":        return self._fiverr_title()
        elif intent == "fiverr_tags":         return self._fiverr_tags()
        elif intent == "fiverr_description":  return self._fiverr_description()
        elif intent == "fiverr_competitor":   return self._fiverr_competitor(entities, raw)
        elif intent == "fiverr_pricing":      return self._fiverr_pricing(entities, raw)
        elif intent == "fiverr_report":       return self._fiverr_report()
        elif intent == "schedule_task":       return self._schedule(raw)
        elif intent == "help":
            self._show_help(); return "help"
        elif intent == "stop":
            self.voice.speak("Khuda Hafiz!"); self._shutdown(); return "stop"
        else:
            self.voice.speak("Samajh nahi aaya — 'help' likhein")
            return "unknown"

    # ═══════════════════════════════════════════════════════════
    # PHASE 1 ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _greeting(self) -> str:
        self.voice.speak(
            "Salam! Main ARIA hun — Phase 1 aur 2 ready. Kya kar sakta hun?"
        )
        self._show_capabilities(); return "greeting"

    def _screenshot(self) -> str:
        self.voice.speak("Screenshot le raha hun...")
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(OUTPUTS_DIR / "screenshots" / f"screenshot_{ts}.png")
        r    = self.apps.take_screenshot(path)
        if r and not r.startswith("Error"):
            self.voice.speak("Screenshot le liya!")
            console.print(f"[green]✅ {r}[/green]")
        else:
            self.voice.speak("Screenshot nahi ho saka")
        return r

    def _screenshot_scheduled(self, raw: str) -> str:
        """Scheduled screenshots start/stop."""
        import re
        stop_words = ["band", "stop", "rokk", "cancel"]
        if any(w in raw.lower() for w in stop_words):
            r = self.apps.stop_scheduled_screenshots()
            self.voice.speak(r["message"])
            return r["message"]

        m        = re.search(r'(\d+)\s*(?:minute|min|ghante|hour)', raw.lower())
        interval = int(m.group(1)) if m else 30
        if "ghante" in raw.lower() or "hour" in raw.lower():
            interval *= 60

        r = self.apps.start_scheduled_screenshots(interval_minutes=interval)
        self.voice.speak(r["message"])
        console.print(f"[green]✅ {r['message']}[/green]")
        return r["message"]

    def _diagnostics(self) -> str:
        """Full system diagnostics."""
        self.voice.speak("Poora system check kar raha hun...")
        diag = self.apps.run_diagnostics()

        # Packages table
        table = Table(title="🔧 ARIA Diagnostics", style="cyan")
        table.add_column("Component")
        table.add_column("Status")

        for name, status in diag.get("packages", {}).items():
            color = "green" if "✅" in status else "red"
            table.add_row(name, f"[{color}]{status}[/{color}]")
        console.print(table)

        # Config
        console.print("\n[bold]🔑 API Keys & Config:[/bold]")
        for k, v in diag.get("config", {}).items():
            color = "green" if "✅" in v else "yellow"
            console.print(f"  [{color}]{v}[/{color}] {k}")

        # Overall
        overall = diag.get("overall", {})
        score   = overall.get("score", "N/A")
        issues  = overall.get("issues", [])
        console.print(
            f"\n[bold]Health Score: [cyan]{score}[/cyan][/bold]"
        )
        if issues:
            console.print(
                f"[yellow]Issues: {', '.join(issues[:3])}[/yellow]"
            )
            self.voice.speak(
                f"Diagnostics complete. Score {score}. "
                f"{len(issues)} issues mili hain."
            )
        else:
            self.voice.speak(
                f"Diagnostics complete. Sab kuch theek hai! Score {score}."
            )
        return score

    def _system_status(self) -> str:
        self.voice.speak("System check kar raha hun...")
        s = self.apps.get_system_status()
        self._render_status(s)
        return "status_shown"

    def _app_open(self, entities, raw) -> str:
        app = entities.get("app_name") or self._get_app(raw)
        if not app:
            self.voice.speak("Kaunsa app kholna hai?")
            app = input("App: ").strip()
        r = self.apps.open_app(app)
        self.voice.speak(r["message"]); return r["message"]

    def _app_close(self, entities, raw) -> str:
        app = entities.get("app_name") or self._get_app(raw)
        if app:
            r = self.apps.close_app(app)
            self.voice.speak(r["message"])
        return app or ""

    def _file_search(self, entities, raw) -> str:
        q     = entities.get("filename", "") or self._qwords(raw)
        ftype = self._ftype(raw)
        res   = self.files.search_files(q, file_type=ftype)
        self._render_files(res)
        self.voice.speak(f"{len(res)} files mili!")
        return str(len(res))

    def _file_organize(self, entities, raw) -> str:
        folder = entities.get("folder", "Downloads")
        fp     = str(Path.home() / folder.capitalize())
        prev   = self.files.organize_folder(fp, dry_run=True)
        count  = prev.get("files_organized", 0)
        self.voice.speak(f"{count} files hain. Organize karun?")
        if self._ok(f"{count} files organize karein?"):
            r = self.files.organize_folder(fp)
            self.voice.speak(f"Ho gaya! {r.get('files_organized',0)} files!")
        return folder

    def _find_duplicates(self, entities, raw) -> str:
        folder = entities.get("folder", "Downloads")
        fp     = str(Path.home() / folder.capitalize())
        dups   = self.files.find_duplicates(fp)
        if dups:
            t = Table(title=f"🔁 Duplicates ({len(dups)})", style="yellow")
            t.add_column("File"); t.add_column("Size")
            t.add_column("Location 1"); t.add_column("Location 2")
            for d in dups[:10]:
                t.add_row(d["name"], d["size"],
                          str(Path(d["original"]).parent)[:35],
                          str(Path(d["duplicate"]).parent)[:35])
            console.print(t)
        self.voice.speak(f"{len(dups)} duplicate files mili!")
        return str(len(dups))

    def _pdf_merge(self) -> str:
        self.voice.speak("PDF paths enter karein (comma se alag karein):")
        paths_str = input("PDF paths: ").strip()
        if paths_str:
            paths = [p.strip() for p in paths_str.split(",")]
            out   = self.files.merge_pdfs(paths)
            self.voice.speak(f"PDFs merge ho gayi!")
            console.print(f"[green]✅ {out}[/green]")
            return out
        return ""

    def _file_create(self, raw: str) -> str:
        import re
        m    = re.search(r'(?:folder|directory)\s+(\w+)', raw, re.I)
        name = m.group(1) if m else input("Folder name: ").strip()
        r    = self.files.create_folder(name)
        self.voice.speak(f"'{name}' ban gaya!")
        return r

    def _email_draft(self, entities, raw) -> str:
        recip = (entities.get("recipient")
                 or self._person(raw)
                 or input("Recipient name: ").strip())
        d = self.email_p1.draft_email(recip, context=raw)
        if d["success"]:
            self._render_email(d)
            self._current_draft = d
            self.voice.speak(f"{recip} ke liye email draft ho gaya!")
        return d.get("subject", "")

    def _volume(self, raw) -> str:
        action = ("mute"  if any(w in raw.lower() for w in ["mute","silent","band"]) else
                  "up"    if any(w in raw.lower() for w in ["up","barhao","increase"]) else
                  "down")
        r = self.apps.control_volume(action)
        self.voice.speak(r["message"]); return action

    def _time(self) -> str:
        now = datetime.now()
        t   = now.strftime("%I:%M %p"); d = now.strftime("%d %B %Y, %A")
        self.voice.speak(f"Abhi {t} baj rahe hain. Aaj {d}.")
        console.print(f"[cyan]🕐 {t}  📅 {d}[/cyan]")
        return f"{t} | {d}"

    # ═══════════════════════════════════════════════════════════
    # PHASE 2 ACTIONS
    # ═══════════════════════════════════════════════════════════

    def _whatsapp_send(self, entities, raw) -> str:
        import re
        m      = re.search(r'\b(0\d{10}|\+92\d{10})\b', raw)
        number = m.group(1) if m else entities.get("phone", "")
        if not number:
            c = self._person(raw)
            if c:
                ct = self.memory.find_contact(c)
                if ct:
                    number = ct.get("whatsapp") or ct.get("phone", "")
        if not number:
            self.voice.speak("Phone number batao:")
            number = input("Number (e.g. 03001234567): ").strip()

        # Message extract
        msg = ""
        for pat in [r'message\s+["\']?(.+?)["\']?\s*$',
                    r'(?:ko|pe)\s+(?:message|msg)\s+["\']?(.+?)["\']?\s*$']:
            mm = re.search(pat, raw, re.IGNORECASE)
            if mm:
                msg = mm.group(1).strip(); break
        if not msg:
            self.voice.speak("Kya message bhejun?")
            msg = input("Message: ").strip()

        fmt = self.whatsapp.format_display(number)
        console.print(Panel(
            f"[bold]To:[/bold] {fmt}\n[bold]Message:[/bold] {msg}",
            title="📱 WhatsApp Preview", style="green"
        ))
        if not self._ok("Yeh message bhejun?"):
            return "cancelled"

        r = self.whatsapp.send_message(number, msg, confirmed=True,
                                        recipient_name=self._person(raw))
        if r["success"]:
            self.voice.speak(f"WhatsApp message bhej diya {fmt} ko!")
        else:
            self.voice.speak(r.get("message", "Nahi bheja"))
        return r.get("response", "")

    def _whatsapp_bulk(self, raw: str) -> str:
        """Sab clients ko WhatsApp message bhejo."""
        contacts = self.memory.get_all_contacts()
        if not contacts:
            self.voice.speak("Koi contacts nahi hain database mein")
            return "no_contacts"

        console.print(
            f"[yellow]{len(contacts)} contacts hain:[/yellow]"
        )
        for c in contacts[:5]:
            console.print(f"  • {c['name']} — {c.get('phone','no phone')}")
        if len(contacts) > 5:
            console.print(f"  ... aur {len(contacts)-5}")

        self.voice.speak(
            f"{len(contacts)} contacts ko message bhejun? Message type karein:"
        )
        msg = input("Bulk message ({name} se personalize hoga): ").strip()
        if not msg:
            return "no_message"

        if not self._ok(
            f"Sab {len(contacts)} contacts ko yeh message bhejun?"
        ):
            return "cancelled"

        result = self.whatsapp.send_bulk(contacts, msg)
        self.voice.speak(
            f"Bulk send complete! {result['success_count']}/{result['total']} bheje!"
        )
        return f"{result['success_count']} sent"

    def _email_send(self, entities, raw) -> str:
        if self._current_draft:
            self._render_email(self._current_draft)
            to = input(
                f"Email address ({self._current_draft['recipient']}): "
            ).strip()
            if "@" not in to:
                self.voice.speak("Valid email address chahiye"); return ""
            if not self._ok(f"Email bhejun {to} ko?"):
                return "cancelled"
            r = self.gmail.send_email(
                to, self._current_draft["subject"],
                self._current_draft["body"]
            )
            if r["success"]:
                self.memory.log_email(
                    to, self._current_draft["subject"],
                    self._current_draft["body"][:200],
                    r.get("message_id")
                )
                self.voice.speak(f"Email bhej diya!")
                self._current_draft = None
            else:
                self.voice.speak(r.get("message", "Error"))
            return r.get("response", "")

        # Inbox check shortcut
        if any(w in raw.lower() for w in
               ["inbox","check","dekho","naye emails"]):
            return self._inbox_check()

        return self._email_draft(entities, raw)

    def _inbox_check(self) -> str:
        self.voice.speak("Inbox check kar raha hun...")
        emails = self.gmail.check_inbox(10)
        if not emails:
            self.voice.speak("Inbox empty ya Gmail connected nahi")
            return "empty"
        t = Table(title=f"📬 Inbox ({len(emails)})", style="blue")
        t.add_column("#", width=3); t.add_column("From")
        t.add_column("Subject"); t.add_column("Date"); t.add_column("R", width=3)
        for i, e in enumerate(emails, 1):
            t.add_row(str(i), e["from"][:28], e["subject"][:38],
                      e["date"][:16], "🔵" if e["unread"] else "  ")
        console.print(t)
        unread = sum(1 for e in emails if e["unread"])
        self.voice.speak(f"{len(emails)} emails, {unread} unread!")
        return f"{len(emails)} emails"

    def _email_reply(self) -> str:
        """AI se email reply suggest karo."""
        emails = self.gmail.check_inbox(5)
        if not emails:
            self.voice.speak("Inbox empty"); return ""
        t = Table(title="Kis email ka reply?", style="blue")
        t.add_column("#"); t.add_column("From"); t.add_column("Subject")
        for i, e in enumerate(emails, 1):
            t.add_row(str(i), e["from"][:30], e["subject"][:40])
        console.print(t)
        choice = input("Number enter karein: ").strip()
        try:
            idx   = int(choice) - 1
            email = self.gmail.read_email(emails[idx]["id"])
            hint  = input("Reply mein kya kehna hai? (optional): ").strip()
            reply = self.gmail.suggest_reply(email, hint)
            if reply["success"]:
                console.print(Panel(
                    reply["reply"],
                    title=f"📧 Suggested Reply — {reply['subject']}",
                    style="green"
                ))
                self.voice.speak("Reply ready hai! Bhejun?")
                if self._ok("Yeh reply bhejun?"):
                    r = self.gmail.send_email(
                        reply["to"], reply["subject"], reply["reply"]
                    )
                    self.voice.speak(
                        "Reply bhej di!" if r["success"] else "Error"
                    )
        except (ValueError, IndexError):
            self.voice.speak("Valid number enter karein")
        return "reply_done"

    def _email_search(self, raw: str) -> str:
        """Ahmed ki email dhoondo → Gmail search."""
        name = self._person(raw) or input("Kiska email dhoondna hai? ").strip()
        query  = f"from:{name}" if name else input("Search query: ").strip()
        self.voice.speak(f"'{name}' ki emails dhoond raha hun...")
        emails = self.gmail.search_emails(query)
        if not emails:
            self.voice.speak("Koi email nahi mili")
            return "none"
        t = Table(title=f"🔍 '{name}' emails ({len(emails)})", style="blue")
        t.add_column("#"); t.add_column("From")
        t.add_column("Subject"); t.add_column("Date")
        for i, e in enumerate(emails, 1):
            t.add_row(str(i), e["from"][:28],
                      e["subject"][:38], e["date"][:16])
        console.print(t)
        self.voice.speak(f"{len(emails)} emails mili hain!")
        return str(len(emails))

    def _file_send(self, entities, raw) -> str:
        import re
        q = entities.get("filename", "") or self._qwords(raw)
        if any(w in raw.lower() for w in ["whatsapp","wa","phone"]):
            m = re.search(r'\b(0\d{10}|\+92\d{10})\b', raw)
            n = m.group(1) if m else input("WhatsApp number: ").strip()
            if not self._ok(f"'{q}' WhatsApp pe bhejun?"):
                return "cancelled"
            r = self.sender.send_file_whatsapp(q, n)
        else:
            email = input("Email address: ").strip()
            if not self._ok(f"'{q}' email se bhejun?"):
                return "cancelled"
            r = self.sender.send_file_email(q, email)
        self.voice.speak("File bhej di!" if r["success"]
                         else r.get("message", "Error"))
        return r.get("response", "")

    def _folder_send(self, raw: str) -> str:
        folder = input("Folder path: ").strip()
        email  = input("Email address: ").strip()
        if not self._ok(f"Folder zip karke {email} ko bhejun?"):
            return "cancelled"
        r = self.sender.zip_and_send_email(folder, email)
        self.voice.speak("Folder bhej diya!" if r["success"]
                         else r.get("message", "Error"))
        return r.get("response", "")

    # ── Fiverr sub-commands ───────────────────────────────────

    def _fiverr_keywords(self, entities, raw) -> str:
        cat = (entities.get("fiverr_category")
               or input("Category (e.g. logo design): ").strip())
        self.voice.speak(f"{cat} ke keywords dhoond raha hun...")
        r   = self.fiverr.get_keywords(cat)
        if r["success"]:
            t = Table(title=f"🔑 Keywords — {cat}", style="green")
            t.add_column("Keyword", style="bold")
            t.add_column("Difficulty"); t.add_column("Volume")
            t.add_column("Type")
            for kw in r.get("keywords", [])[:20]:
                c = ("green" if kw["difficulty"]=="low" else
                     "yellow" if kw["difficulty"]=="medium" else "red")
                t.add_row(kw["keyword"],
                          f"[{c}]{kw['difficulty']}[/{c}]",
                          kw["volume"], kw["type"])
            console.print(t)
            top3 = r.get("top_3", [])
            if top3:
                console.print(f"[bold green]⭐ Top 3:[/bold green] {', '.join(top3)}")
            console.print(f"[yellow]💡 {r.get('tip','')}[/yellow]")
            self.voice.speak(
                f"{len(r.get('keywords',[]))} keywords mili! Top: {top3[0] if top3 else ''}"
            )
        return cat

    def _fiverr_freq(self) -> str:
        """Keyword frequency analyzer."""
        self.voice.speak(
            "Competitor titles paste karein (ek ek line mein, END type karein):"
        )
        console.print("[yellow]Competitor gig titles enter karein "
                      "(ek per line, phir 'END'):[/yellow]")
        samples = []
        while True:
            line = input("> ").strip()
            if line.upper() == "END" or not line:
                break
            samples.append(line)

        if not samples:
            self.voice.speak("Koi titles enter nahi kiye")
            return ""

        r = self.fiverr.analyze_keyword_frequency(samples)
        if r["success"]:
            t = Table(
                title=f"📊 Keyword Frequency ({r['samples_analyzed']} titles)",
                style="cyan"
            )
            t.add_column("Keyword"); t.add_column("Count"); t.add_column("%")
            for kw in r.get("top_keywords", [])[:15]:
                t.add_row(kw["keyword"], str(kw["frequency"]),
                          f"{kw['percentage']}%")
            console.print(t)

            console.print("\n[bold]Top Phrases:[/bold]")
            for ph in r.get("top_phrases", [])[:5]:
                console.print(f"  • {ph['phrase']} ({ph['frequency']}x)")

            console.print(f"\n[yellow]💡 {r.get('recommendation','')}[/yellow]")
            self.voice.speak(
                f"Analysis complete! {r['total_unique_keywords']} unique keywords mili."
            )
        return "freq_done"

    def _fiverr_ranking(self, entities, raw) -> str:
        cat  = (entities.get("fiverr_category")
                or input("Category: ").strip())
        reviews = input("Aapke kitne reviews hain? (0 if new): ").strip()
        stats = {"reviews": int(reviews) if reviews.isdigit() else 0,
                 "level": "new seller" if (int(reviews) if reviews.isdigit() else 0) < 10
                          else "level 1"}
        self.voice.speak("Ranking opportunities dhoond raha hun...")
        r = self.fiverr.detect_ranking_opportunities(cat, stats)
        if r.get("success"):
            console.print(Panel(
                f"[bold]Quick Wins:[/bold] "
                f"{', '.join(r.get('quick_wins', []))}\n\n"
                + "\n".join(
                    f"[cyan]Step {i+1}:[/cyan] {s}"
                    for i, s in enumerate(r.get("action_plan", []))
                ),
                title=f"🎯 Ranking Opportunities — {cat}", style="green"
            ))
            opps = r.get("opportunities", [])
            if opps:
                t = Table(title="Opportunities", style="blue")
                t.add_column("Keyword"); t.add_column("Your Chance")
                t.add_column("Strategy")
                for o in opps[:5]:
                    t.add_row(o["keyword"], o["your_chance"],
                              o.get("strategy","")[:50])
                console.print(t)
            self.voice.speak(
                f"Ranking analysis ho gaya! "
                f"Quick wins: {', '.join(r.get('quick_wins',['N/A'])[:2])}"
            )
        return cat

    def _fiverr_title(self) -> str:
        title = input("Aapka current gig title: ").strip()
        cat   = input("Category: ").strip()
        self.voice.speak("Title optimize kar raha hun...")
        r     = self.fiverr.optimize_gig_title(title, cat)
        if r.get("success"):
            console.print(Panel(
                f"[dim]Original:[/dim] {r['original']}\n\n"
                + "\n".join(
                    f"[green]{i+1}.[/green] {t['title']}\n"
                    f"   [dim]{t['reason']} | Score: {t['score']}/100[/dim]"
                    for i, t in enumerate(r.get("optimized_titles", []))
                ) + f"\n\n[bold green]✅ Best: {r.get('best_pick','')}[/bold green]",
                title="📝 Title Optimizer", style="green"
            ))
            self.voice.speak("Title optimize ho gaya!")
        return title

    def _fiverr_tags(self) -> str:
        title = input("Gig title: ").strip()
        cat   = input("Category: ").strip()
        self.voice.speak("30 tags generate kar raha hun...")
        r     = self.fiverr.generate_tags(title, cat, count=30)
        if r.get("success"):
            tags = r.get("tags", [])
            console.print(Panel(
                "[bold]All Tags:[/bold]\n"
                + ", ".join(f"[cyan]{t}[/cyan]" for t in tags) +
                f"\n\n[bold green]Primary (Top 5):[/bold green] "
                + ", ".join(r.get("primary_tags", [])[:5]) +
                f"\n\n[yellow]💡 {r.get('tip','')}[/yellow]",
                title=f"🏷️ {len(tags)} SEO Tags", style="green"
            ))
            self.voice.speak(f"{len(tags)} tags ready!")
        return title

    def _fiverr_description(self) -> str:
        cat  = input("Category: ").strip()
        desc = input("Current description (paste karein): ").strip()
        if not desc:
            desc = "I will provide professional services for your needs."
        self.voice.speak("Description improve kar raha hun...")
        r    = self.fiverr.enhance_description(desc, cat)
        if r.get("success"):
            console.print(Panel(
                r.get("enhanced_description", ""),
                title="✨ Enhanced Description", style="green"
            ))
            improvements = r.get("improvements_made", [])
            console.print("[bold]Improvements:[/bold]")
            for imp in improvements:
                console.print(f"  ✅ {imp}")
            score = r.get("conversion_score", "N/A")
            console.print(
                f"[cyan]Conversion Score: {score}/100[/cyan]"
            )
            self.voice.speak(
                f"Description enhance ho gaya! Score: {score}/100"
            )
        return "description_done"

    def _fiverr_competitor(self, entities, raw) -> str:
        cat  = (entities.get("fiverr_category")
                or input("Category: ").strip())
        self.voice.speak(f"{cat} ka competitor analyze kar raha hun...")
        r    = self.fiverr.analyze_competitors(cat)
        if r.get("success"):
            ov = r.get("market_overview", {})
            console.print(Panel(
                f"[bold]Competition:[/bold] {ov.get('competition_level','N/A')}\n"
                f"[bold]Avg Basic:[/bold] {ov.get('avg_price_basic','N/A')}\n"
                f"[bold]Avg Standard:[/bold] {ov.get('avg_price_standard','N/A')}\n"
                f"[bold]Saturation:[/bold] {ov.get('market_saturation','N/A')}/100\n\n"
                f"[bold yellow]Your Advantage:[/bold yellow] {r.get('your_advantage','')}\n"
                f"[bold green]Ranking Tip:[/bold green] {r.get('ranking_tip','')}",
                title=f"📊 Competitor — {cat}", style="blue"
            ))
            for s in r.get("winning_strategies", []):
                console.print(f"  ✅ {s}")
            self.voice.speak(
                f"Competitor analysis ho gaya! "
                f"Competition: {ov.get('competition_level','N/A')}"
            )
        return cat

    def _fiverr_pricing(self, entities, raw) -> str:
        cat  = (entities.get("fiverr_category")
                or input("Category: ").strip())
        exp  = input("Experience (beginner/intermediate/expert): ").strip() or "intermediate"
        r    = self.fiverr.pricing_strategy(cat, exp)
        if r.get("success"):
            t = Table(title=f"💰 Pricing Strategy — {cat}", style="green")
            t.add_column("Package"); t.add_column("Price")
            t.add_column("Delivery"); t.add_column("Revisions"); t.add_column("Includes")
            for pkg in ["basic", "standard", "premium"]:
                d = r.get(pkg, {})
                t.add_row(
                    pkg.upper(), d.get("price","N/A"),
                    f"{d.get('delivery_days','?')} days",
                    str(d.get("revisions","?")),
                    ", ".join(d.get("includes", [])[:2])
                )
            console.print(t)
            console.print(
                f"[yellow]💡 {r.get('strategy_tip','')}[/yellow]"
            )
            self.voice.speak("Pricing strategy ready!")
        return cat

    def _fiverr_report(self) -> str:
        self.voice.speak("Fiverr performance report bana raha hun...")
        stats = {}
        console.print(
            "[yellow]Stats enter karein (Enter se skip):[/yellow]"
        )
        for field in ["total_revenue","total_orders","impressions","clicks"]:
            val = input(f"  {field}: ").strip()
            if val.isdigit():
                stats[field] = int(val)

        r = self.fiverr.generate_report(stats)
        if r["success"]:
            report = r["report"]
            console.print(Panel(
                f"Period: {report['period']}\n"
                f"Revenue: ${report['total_revenue']}\n"
                f"Orders: {report['total_orders']}\n"
                f"Conversion: {report['conversion']}\n\n"
                + "\n".join(f"📌 {rec}"
                            for rec in report['recommendations']),
                title="📈 Fiverr Report", style="green"
            ))
            console.print(f"[dim]Saved: {r['saved_at']}[/dim]")
            self.voice.speak(f"Report ban gayi! Saved at outputs/fiverr/")
        return r.get("saved_at", "")

    def _schedule(self, raw: str) -> str:
        console.print("[cyan]Schedule a Task:[/cyan]")
        task_type = input("Type (email/whatsapp/fiverr_report): ").strip() or "email"
        desc      = input("Description: ").strip()
        run_at    = input("Kab? (e.g. 'tomorrow 9am'): ").strip()
        recurring = input("Recurring? (daily/weekly/monday / leave empty): ").strip() or None

        data: dict = {}
        if task_type == "email":
            data = {
                "to_email": input("To: ").strip(),
                "subject":  input("Subject: ").strip(),
                "body":     input("Body: ").strip(),
            }
        elif task_type == "whatsapp":
            data = {
                "to_number": input("Number: ").strip(),
                "message":   input("Message: ").strip(),
            }

        r = self.scheduler.schedule_task(
            task_type, data, run_at=run_at or None,
            recurring=recurring, description=desc
        )
        self.voice.speak(r["message"])
        console.print(f"[green]✅ {r['message']}[/green]")
        return r["task_id"]

    # ═══════════════════════════════════════════════════════════
    # DISPLAY / UTILITY
    # ═══════════════════════════════════════════════════════════

    def _render_status(self, s: dict):
        if "error" in s:
            console.print(f"[red]{s['error']}[/red]"); return
        t = Table(title="💻 System Status", style="cyan")
        t.add_column("Component", style="bold")
        t.add_column("Usage", style="green"); t.add_column("Details")
        cpu  = s.get("cpu",  {})
        ram  = s.get("ram",  {})
        disk = s.get("disk", {})
        bat  = s.get("battery")
        t.add_row("CPU",    cpu.get("usage","N/A"),  f"{cpu.get('cores','?')} cores")
        t.add_row("RAM",    ram.get("percent","N/A"), f"{ram.get('used','?')} / {ram.get('total','?')}")
        t.add_row("Disk",   disk.get("percent","N/A"), f"{disk.get('free','?')} free")
        if bat:
            icon = "🔌" if bat.get("plugged") else "🔋"
            t.add_row("Battery", f"{icon} {bat.get('percent','?')}%", bat.get("status",""))
        console.print(t)
        self.voice.speak(
            f"CPU {cpu.get('usage','?')} use. RAM {ram.get('percent','?')} use."
        )

    def _render_files(self, results: list):
        if not results:
            console.print("[yellow]Koi file nahi mili[/yellow]"); return
        t = Table(title=f"📁 Files ({len(results)})", style="blue")
        t.add_column("#", width=4); t.add_column("Name", style="bold")
        t.add_column("Size"); t.add_column("Modified"); t.add_column("Path", style="dim")
        for i, f in enumerate(results[:15], 1):
            t.add_row(str(i), f["name"], f["size"],
                      f["modified"], str(Path(f["path"]).parent)[:40])
        console.print(t)

    def _render_email(self, d: dict):
        console.print(Panel(
            f"[bold]To:[/bold] {d.get('recipient','')}\n"
            f"[bold]Subject:[/bold] {d.get('subject','')}\n\n"
            f"{d.get('body','')}",
            title="📧 Email Draft", style="green"
        ))

    def _ok(self, msg: str) -> bool:
        console.print(f"\n[yellow]⚠️  {msg}[/yellow]")
        return input("Han/No (h/n): ").lower().strip() in \
               ['h','ha','han','haan','yes','y']

    def _get_app(self, text: str) -> str:
        for a in ["chrome","firefox","notepad","excel","word",
                  "vlc","spotify","vscode","calculator","paint",
                  "explorer","powershell","cmd"]:
            if a in text.lower(): return a
        return ""

    def _ftype(self, text: str) -> str:
        m = {"pdf":"pdf","image":"image","photo":"image","video":"video",
             "document":"document","excel":"spreadsheet","audio":"audio"}
        for k,v in m.items():
            if k in text.lower(): return v
        return ""

    def _qwords(self, text: str) -> str:
        import re
        stop = {"meri","mera","ki","ka","ko","dhoondo","find","search",
                "file","files","karo","chahiye","bhejo","send","email","whatsapp"}
        return " ".join(
            w for w in re.split(r'\s+', text.lower())
            if w not in stop and len(w) > 2
        )[:30]

    def _person(self, text: str) -> str:
        import re
        for pat in [
            r'(\w+)\s+(?:ko|ke liye)\s+(?:email|mail|message|whatsapp)',
            r'(?:dear|to)\s+(\w+)', r'email\s+(\w+)',
            r'(\w+)\s+(?:ki email|ka mail|ki emails)',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                n = m.group(1).capitalize()
                if len(n) > 2 and n.lower() not in {'ko','ke','ka'}:
                    return n
        return ""

    def _show_welcome(self):
        t = Text()
        t.append("🤖 ARIA v2 FINAL\n", style="bold cyan")
        t.append("Phase 1 ✅ + Phase 2 ✅ — ALL FEATURES\n", style="green")
        t.append("Urdu • English • Roman Urdu\n", style="yellow")
        console.print(Panel(t, style="cyan"))
        s = self.memory.get_stats()
        console.print(
            f"[dim]Conversations: {s['total_conversations']} | "
            f"Contacts: {s['total_contacts']} | "
            f"Emails: {s['emails_sent']} | "
            f"WhatsApp: {s['whatsapp_sent']}[/dim]\n"
        )
        self.voice.speak(
            "Salam! ARIA v2 FINAL ready — sab features active. "
            "Help ke liye 'help' likhein."
        )

    def _show_capabilities(self):
        console.print(
            "[bold cyan]Phase 1:[/bold cyan] screenshot • files • apps • system status • email draft • PDF merge • duplicates\n"
            "[bold green]Phase 2:[/bold green] WhatsApp • Gmail send/read/reply/search • Fiverr keywords/tags/title/description/competitor/pricing/report • File send • Scheduler\n"
            "[dim]'help' — full command list[/dim]"
        )

    def _show_help(self):
        t = Table(title="📋 ARIA v2 FINAL — All Commands", style="green")
        t.add_column("Command", style="bold yellow")
        t.add_column("Ph"); t.add_column("Action")
        cmds = [
            ("hello aria",                     "1","Greeting"),
            ("screenshot lo",                  "1","Screen capture"),
            ("screenshot har 30 min lo",       "1","Scheduled screenshots"),
            ("diagnostics run karo",           "1","Full system health check"),
            ("system status batao",            "1","CPU/RAM/Battery/Disk"),
            ("meri pdf files dhoondo",         "1","File search"),
            ("Downloads organize karo",        "1","Folder organize"),
            ("duplicate files dhoondo",        "1","Duplicates"),
            ("chrome kholo / band karo",       "1","App control"),
            ("ahmed ko email likho",           "1","AI email draft"),
            ("---Phase 2---",                  "",""),
            ("03001234567 ko message bhejo",   "2","WhatsApp send + DB log"),
            ("sab clients ko update bhejo",    "2","WhatsApp bulk"),
            ("email bhejo",                    "2","Gmail send"),
            ("inbox check karo",               "2","Gmail inbox"),
            ("is email ka reply likho",        "2","AI email reply"),
            ("ahmed ki email dhoondo",         "2","Gmail search"),
            ("cv.pdf email bhejo",             "2","File auto-send"),
            ("project folder email karo",      "2","Folder zip + send"),
            ("logo design ke keywords do",     "2","Fiverr keywords (30)"),
            ("keyword frequency analyze karo", "2","Frequency analyzer"),
            ("ranking opportunity dhoondo",    "2","Ranking detector"),
            ("gig title optimize karo",        "2","Title optimizer"),
            ("30 tags suggest karo",           "2","SEO tags"),
            ("description improve karo",       "2","Description enhancer"),
            ("competitor analyze karo",        "2","Competitor analysis"),
            ("pricing strategy do",            "2","Pricing comparison"),
            ("fiverr report banao",            "2","PDF performance report"),
            ("kal 9 baje email schedule karo", "2","Task scheduler"),
        ]
        for cmd, ph, action in cmds:
            if cmd.startswith("---"):
                t.add_row("", "", "")
                continue
            c = "green" if ph == "2" else "cyan" if ph == "1" else "white"
            t.add_row(f'"{cmd}"', f"[{c}]{ph}[/{c}]", action)
        console.print(t)

    def _shutdown(self):
        self._running = False
        self.scheduler.stop_background()
        console.print("[yellow]\n👋 Khuda Hafiz! ARIA band ho rahi hai.[/yellow]")


def main():
    import argparse
    p = argparse.ArgumentParser(description="ARIA v2 FINAL")
    p.add_argument("--voice", "-v", action="store_true")
    args = p.parse_args()
    ARIAv2().run(use_voice=args.voice)


if __name__ == "__main__":
    main()
