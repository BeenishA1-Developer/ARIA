"""
ARIA v3 — Beautiful GUI Launcher
Ek button dabao → ARIA on ho jaye
Voice + Chat interface
"""

import sys
import os
import threading
import queue
import time
from pathlib import Path
from datetime import datetime

# ── Add project to path ──────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

import tkinter as tk
from tkinter import scrolledtext, font
import tkinter.ttk as ttk

# ── Try importing ARIA ───────────────────────────────────────
ARIA_READY = False
aria_instance = None

# ── Message Queue for thread-safe GUI updates ────────────────
msg_queue = queue.Queue()

# ─────────────────────────────────────────────────────────────
# COLORS & THEME
# ─────────────────────────────────────────────────────────────
BG        = "#0d0d1a"
BG2       = "#1a1a2e"
BG3       = "#16213e"
ACCENT    = "#00d4ff"
ACCENT2   = "#7c3aed"
GREEN     = "#00ff88"
RED       = "#ff4757"
YELLOW    = "#ffd700"
TEXT      = "#e0e0ff"
TEXT_DIM  = "#888aaa"
ARIA_CLR  = "#00d4ff"
USER_CLR  = "#7c3aed"
MSG_BG    = "#1e1e3a"

# ─────────────────────────────────────────────────────────────
# ARIA BACKEND THREAD
# ─────────────────────────────────────────────────────────────

class ARIABackend(threading.Thread):
    def __init__(self, msg_q):
        super().__init__(daemon=True)
        self.q        = msg_q
        self.input_q  = queue.Queue()
        self.running  = False

    def run(self):
        self.q.put(("status", "loading", "ARIA load ho rahi hai..."))
        try:
            from core.master_executor_v3 import ARIAv3
            global aria_instance
            aria_instance = ARIAv3()
            self.running  = True
            self.q.put(("status", "ready", "✅ ARIA Ready!"))
            self.q.put(("aria", "Salam! 👋 Main ARIA hun — aapki AI assistant. Kya kar sakti hun aapke liye?"))
        except Exception as e:
            self.q.put(("status", "error", f"Load error: {e}"))
            return

        # Main conversation loop
        while self.running:
            try:
                user_input = self.input_q.get(timeout=0.5)
                if user_input == "__STOP__":
                    break
                if not user_input.strip():
                    continue

                # Process through ARIA
                try:
                    from core.nlp_engine import NLPEngine
                    result   = aria_instance.nlp.detect_intent(user_input)
                    intent   = result["intent"]
                    entities = result["entities"]

                    # Get response
                    response = aria_instance._route(intent, entities, user_input)

                    # Save to memory
                    aria_instance.memory.save_conversation(
                        user_input, response or "", intent, "gui_session"
                    )

                    if not response:
                        response = "Theek hai! Kuch aur chahiye?"

                    self.q.put(("aria", str(response)))

                except Exception as e:
                    self.q.put(("aria", f"Maafi chahti hun — kuch error aa gayi: {str(e)[:80]}"))

            except queue.Empty:
                continue
            except Exception:
                continue

    def send(self, text):
        self.input_q.put(text)

    def stop(self):
        self.running = False
        self.input_q.put("__STOP__")

# ─────────────────────────────────────────────────────────────
# MAIN GUI
# ─────────────────────────────────────────────────────────────

class ARIAGui:
    def __init__(self):
        self.root    = tk.Tk()
        self.backend = None
        self.is_on   = False
        self._build_ui()
        self._poll_queue()
        self.root.mainloop()

    def _build_ui(self):
        self.root.title("🤖 ARIA v3 — AI Assistant")
        self.root.geometry("800x680")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        # ── HEADER ──────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG3, height=70)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(
            hdr, text="🤖  ARIA",
            font=("Segoe UI", 22, "bold"),
            bg=BG3, fg=ACCENT
        ).pack(side="left", padx=20, pady=12)

        tk.Label(
            hdr, text="AI Personal Assistant  •  Phase 1 + 2 + 3",
            font=("Segoe UI", 10), bg=BG3, fg=TEXT_DIM
        ).pack(side="left", pady=18)

        # Status badge
        self.status_label = tk.Label(
            hdr, text="⏸ OFF",
            font=("Segoe UI", 11, "bold"),
            bg=BG3, fg=RED, padx=12
        )
        self.status_label.pack(side="right", padx=20)

        # ── CHAT AREA ───────────────────────────────────────
        chat_frame = tk.Frame(self.root, bg=BG)
        chat_frame.pack(fill="both", expand=True, padx=15, pady=(10, 5))

        self.chat = scrolledtext.ScrolledText(
            chat_frame,
            bg=BG2, fg=TEXT,
            font=("Segoe UI", 11),
            relief="flat", bd=0,
            wrap="word",
            state="disabled",
            insertbackground=ACCENT,
            selectbackground=ACCENT2,
        )
        self.chat.pack(fill="both", expand=True)

        # Text tags for colors
        self.chat.tag_config("aria_name",  foreground=ACCENT,  font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("aria_text",  foreground=TEXT,    font=("Segoe UI", 11))
        self.chat.tag_config("user_name",  foreground=USER_CLR, font=("Segoe UI", 10, "bold"))
        self.chat.tag_config("user_text",  foreground="#c9b8ff", font=("Segoe UI", 11))
        self.chat.tag_config("system",     foreground=YELLOW,  font=("Segoe UI", 10, "italic"))
        self.chat.tag_config("time",       foreground=TEXT_DIM, font=("Segoe UI", 9))

        # ── WELCOME MESSAGE ──────────────────────────────────
        self._add_system("Neeche wala bada button dabao — ARIA on ho jaegi! 🚀")

        # ── INPUT AREA ──────────────────────────────────────
        input_frame = tk.Frame(self.root, bg=BG3, pady=10)
        input_frame.pack(fill="x", side="bottom")

        # Inner frame for centering
        inner = tk.Frame(input_frame, bg=BG3)
        inner.pack(fill="x", padx=15)

        # Text input
        self.input_var = tk.StringVar()
        self.entry = tk.Entry(
            inner,
            textvariable=self.input_var,
            font=("Segoe UI", 13),
            bg=BG2, fg=TEXT,
            insertbackground=ACCENT,
            relief="flat", bd=8,
            state="disabled",
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.entry.bind("<Return>", self._send_text)

        # Send button
        self.send_btn = tk.Button(
            inner, text="➤",
            font=("Segoe UI", 14, "bold"),
            bg=ACCENT2, fg="white",
            relief="flat", bd=0, padx=18,
            cursor="hand2",
            activebackground="#5b21b6",
            state="disabled",
            command=self._send_text,
        )
        self.send_btn.pack(side="left", padx=(8, 0), ipady=6)

        # ── BIG ON/OFF BUTTON ───────────────────────────────
        btn_frame = tk.Frame(self.root, bg=BG, pady=12)
        btn_frame.pack(side="bottom", fill="x")

        self.toggle_btn = tk.Button(
            btn_frame,
            text="▶  ARIA ON KARO",
            font=("Segoe UI", 16, "bold"),
            bg=GREEN, fg="#001a00",
            relief="flat", bd=0,
            padx=40, pady=14,
            cursor="hand2",
            activebackground="#00cc66",
            command=self._toggle_aria,
        )
        self.toggle_btn.pack()

        # Hint label
        tk.Label(
            btn_frame, text="Ek click — aur ARIA taiyaar!",
            font=("Segoe UI", 9), bg=BG, fg=TEXT_DIM
        ).pack(pady=(2, 0))

    # ── ADD MESSAGES ────────────────────────────────────────

    def _add_aria(self, text):
        self.chat.configure(state="normal")
        t = datetime.now().strftime("%I:%M %p")
        self.chat.insert("end", f"\n🤖 ARIA  ", "aria_name")
        self.chat.insert("end", f"[{t}]\n", "time")
        self.chat.insert("end", f"   {text}\n", "aria_text")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _add_user(self, text):
        self.chat.configure(state="normal")
        t = datetime.now().strftime("%I:%M %p")
        self.chat.insert("end", f"\n👤 Aap  ", "user_name")
        self.chat.insert("end", f"[{t}]\n", "time")
        self.chat.insert("end", f"   {text}\n", "user_text")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _add_system(self, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"\n⚡ {text}\n", "system")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    # ── TOGGLE ARIA ON/OFF ──────────────────────────────────

    def _toggle_aria(self):
        if not self.is_on:
            self._start_aria()
        else:
            self._stop_aria()

    def _start_aria(self):
        self.toggle_btn.config(
            text="⏳  Loading...", bg="#555", state="disabled"
        )
        self.status_label.config(text="⏳ Loading...", fg=YELLOW)
        self._add_system("ARIA load ho rahi hai — thora intezaar karein...")

        self.backend = ARIABackend(msg_queue)
        self.backend.start()

    def _stop_aria(self):
        if self.backend:
            self.backend.stop()
        self.is_on = False
        self.toggle_btn.config(
            text="▶  ARIA ON KARO", bg=GREEN,
            fg="#001a00", state="normal"
        )
        self.status_label.config(text="⏸ OFF", fg=RED)
        self.entry.config(state="disabled")
        self.send_btn.config(state="disabled")
        self._add_system("ARIA band ho gayi. Button dabao dobara start karne ke liye.")

    # ── SEND TEXT ───────────────────────────────────────────

    def _send_text(self, event=None):
        text = self.input_var.get().strip()
        if not text or not self.is_on:
            return
        self._add_user(text)
        self.input_var.set("")

        if text.lower() in ["stop", "exit", "quit", "bye", "band ho jao"]:
            self._stop_aria()
            return

        self.backend.send(text)
        self.toggle_btn.config(state="disabled")
        self._add_system("Soch rahi hun...")

    # ── POLL QUEUE (main thread) ─────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                item = msg_queue.get_nowait()

                if item[0] == "status":
                    _, state, msg = item
                    if state == "ready":
                        self.is_on = True
                        self.toggle_btn.config(
                            text="⏹  ARIA BAND KARO",
                            bg=RED, fg="white", state="normal"
                        )
                        self.status_label.config(text="🟢 ON", fg=GREEN)
                        self.entry.config(state="normal")
                        self.send_btn.config(state="normal")
                        self.entry.focus()
                        self._add_system(msg)
                    elif state == "loading":
                        self._add_system(msg)
                    elif state == "error":
                        self._add_system(f"❌ {msg}")
                        self.toggle_btn.config(
                            text="▶  ARIA ON KARO",
                            bg=GREEN, fg="#001a00", state="normal"
                        )
                        self.status_label.config(text="❌ Error", fg=RED)

                elif item[0] == "aria":
                    # Remove "Soch rahi hun..." line if present
                    self.chat.configure(state="normal")
                    content = self.chat.get("1.0", "end")
                    if "Soch rahi hun..." in content:
                        idx = self.chat.search(
                            "⚡ Soch rahi hun...", "1.0", "end"
                        )
                        if idx:
                            line_end = f"{idx} lineend+1c"
                            self.chat.delete(idx, line_end)
                    self.chat.configure(state="disabled")

                    self._add_aria(item[1])
                    self.toggle_btn.config(state="normal")

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_queue)


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ARIAGui()
