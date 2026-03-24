# ============================================================
# ARIA - Memory System v2
# SQLite (structured) + ChromaDB (semantic/vector search)
# ============================================================

import sqlite3
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from loguru import logger

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not installed — semantic search disabled")


class MemorySystem:
    """
    ARIA Memory System — SQLite + ChromaDB.
    SQLite  : conversations, contacts, emails, tasks, file logs
    ChromaDB: semantic search — "Ahmed ka project" → finds Ahmed related data
    """

    def __init__(self, db_path: str = "data/aria_memory.db",
                 chroma_path: str = "data/chroma_db"):
        self.db_path     = db_path
        self.chroma_path = chroma_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()
        self._chroma_client     = None
        self._chroma_collection = None
        self._init_chroma()
        logger.info("Memory System v2 initialized (SQLite + ChromaDB)")

    # ── SQLITE INIT ───────────────────────────────────────────

    def _init_sqlite(self):
        conn = self._conn()
        c    = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_input TEXT NOT NULL,
            aria_response TEXT NOT NULL,
            intent TEXT,
            session_id TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT, phone TEXT, whatsapp TEXT, notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL, subject TEXT NOT NULL,
            body_preview TEXT, sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent', gmail_message_id TEXT,
            channel TEXT DEFAULT 'email'
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, description TEXT,
            scheduled_time TEXT, status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS file_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation TEXT NOT NULL, file_path TEXT NOT NULL,
            destination TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            success INTEGER DEFAULT 1
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS whatsapp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_number TEXT NOT NULL,
            recipient_name TEXT,
            message TEXT NOT NULL,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'sent',
            twilio_sid TEXT,
            is_bulk INTEGER DEFAULT 0
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
        conn.close()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    # ── CHROMADB INIT ─────────────────────────────────────────

    def _init_chroma(self):
        """ChromaDB semantic memory initialize karo."""
        if not CHROMA_AVAILABLE:
            return
        try:
            Path(self.chroma_path).mkdir(parents=True, exist_ok=True)
            self._chroma_client = chromadb.PersistentClient(
                path=self.chroma_path
            )
            self._chroma_collection = self._chroma_client.get_or_create_collection(
                name="aria_memory",
                metadata={"hnsw:space": "cosine"}
            )
            logger.success("ChromaDB semantic memory ready!")
        except Exception as e:
            logger.warning(f"ChromaDB init failed: {e}")
            self._chroma_client     = None
            self._chroma_collection = None

    def add_to_semantic_memory(self, text: str, metadata: dict = None,
                                doc_id: str = None):
        """
        Semantic memory mein add karo — ChromaDB.
        Baad mein 'Ahmed ka project' se dhundh sakte hain.
        """
        if not self._chroma_collection:
            return
        try:
            uid = doc_id or f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            self._chroma_collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[uid]
            )
        except Exception as e:
            logger.debug(f"Semantic add error: {e}")

    def semantic_search(self, query: str, n_results: int = 5) -> list:
        """
        Semantic search — meaning se dhoondho.
        "Ahmed ka kaam" → finds Ahmed related conversations
        """
        if not self._chroma_collection:
            return []
        try:
            results = self._chroma_collection.query(
                query_texts=[query],
                n_results=min(n_results,
                              self._chroma_collection.count() or 1)
            )
            docs      = results.get("documents",  [[]])[0]
            metas     = results.get("metadatas",  [[]])[0]
            distances = results.get("distances",  [[]])[0]
            return [
                {"text": d, "metadata": m,
                 "relevance": round(1 - dist, 3)}
                for d, m, dist in zip(docs, metas, distances)
            ]
        except Exception as e:
            logger.debug(f"Semantic search error: {e}")
            return []

    # ── CONVERSATIONS ─────────────────────────────────────────

    def save_conversation(self, user_input: str, aria_response: str,
                          intent: str = None, session_id: str = None):
        conn = self._conn()
        conn.execute(
            '''INSERT INTO conversations
               (timestamp, user_input, aria_response, intent, session_id)
               VALUES (?,?,?,?,?)''',
            (datetime.now().isoformat(), user_input,
             aria_response, intent, session_id)
        )
        conn.commit(); conn.close()

        # Also add to semantic memory
        self.add_to_semantic_memory(
            text=f"User: {user_input} | ARIA: {aria_response}",
            metadata={"type": "conversation", "intent": intent or ""},
        )

    def get_recent_conversations(self, limit: int = 10) -> list:
        conn = self._conn()
        rows = conn.execute(
            'SELECT * FROM conversations ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── CONTACTS ──────────────────────────────────────────────

    def save_contact(self, name: str, email: str = None,
                     phone: str = None, whatsapp: str = None,
                     notes: str = None) -> int:
        conn = self._conn()
        ex   = conn.execute(
            'SELECT id FROM contacts WHERE LOWER(name)=LOWER(?)', (name,)
        ).fetchone()

        if ex:
            conn.execute(
                '''UPDATE contacts
                   SET email=COALESCE(?,email),
                       phone=COALESCE(?,phone),
                       whatsapp=COALESCE(?,whatsapp),
                       notes=COALESCE(?,notes),
                       updated_at=?
                   WHERE id=?''',
                (email, phone, whatsapp, notes,
                 datetime.now().isoformat(), ex['id'])
            )
            cid = ex['id']
        else:
            cur = conn.execute(
                '''INSERT INTO contacts (name,email,phone,whatsapp,notes)
                   VALUES (?,?,?,?,?)''',
                (name, email, phone, whatsapp, notes)
            )
            cid = cur.lastrowid
            # Add to semantic memory
            self.add_to_semantic_memory(
                f"Contact: {name}, email: {email}, phone: {phone}",
                {"type": "contact", "name": name}
            )

        conn.commit(); conn.close()
        logger.info(f"Contact saved: {name}")
        return cid

    def find_contact(self, name: str) -> Optional[dict]:
        conn = self._conn()
        row  = conn.execute(
            'SELECT * FROM contacts WHERE LOWER(name) LIKE LOWER(?)',
            (f'%{name}%',)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_contacts(self) -> list:
        conn = self._conn()
        rows = conn.execute(
            'SELECT * FROM contacts ORDER BY name'
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── EMAIL LOG ─────────────────────────────────────────────

    def log_email(self, recipient: str, subject: str,
                  body_preview: str = None,
                  gmail_message_id: str = None,
                  channel: str = "email"):
        conn = self._conn()
        conn.execute(
            '''INSERT INTO email_log
               (recipient,subject,body_preview,gmail_message_id,channel)
               VALUES (?,?,?,?,?)''',
            (recipient, subject, body_preview,
             gmail_message_id, channel)
        )
        conn.commit(); conn.close()

    def get_email_history(self, limit: int = 20) -> list:
        conn = self._conn()
        rows = conn.execute(
            'SELECT * FROM email_log ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── WHATSAPP LOG ──────────────────────────────────────────

    def log_whatsapp(self, recipient_number: str, message: str,
                     recipient_name: str = None,
                     twilio_sid: str = None,
                     is_bulk: bool = False):
        """WhatsApp message log karo."""
        conn = self._conn()
        conn.execute(
            '''INSERT INTO whatsapp_log
               (recipient_number,recipient_name,message,twilio_sid,is_bulk)
               VALUES (?,?,?,?,?)''',
            (recipient_number, recipient_name, message,
             twilio_sid, int(is_bulk))
        )
        conn.commit(); conn.close()
        logger.info(f"WA logged: {recipient_number}")

    def get_whatsapp_history(self, limit: int = 20) -> list:
        conn = self._conn()
        rows = conn.execute(
            'SELECT * FROM whatsapp_log ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ── TASKS ─────────────────────────────────────────────────

    def add_task(self, title: str, description: str = None,
                 scheduled_time: str = None,
                 priority: int = 1) -> int:
        conn = self._conn()
        cur  = conn.execute(
            '''INSERT INTO tasks (title,description,scheduled_time,priority)
               VALUES (?,?,?,?)''',
            (title, description, scheduled_time, priority)
        )
        tid = cur.lastrowid
        conn.commit(); conn.close()
        return tid

    def get_pending_tasks(self) -> list:
        conn = self._conn()
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status='pending' ORDER BY priority DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def complete_task(self, task_id: int):
        conn = self._conn()
        conn.execute(
            "UPDATE tasks SET status='completed',completed_at=? WHERE id=?",
            (datetime.now().isoformat(), task_id)
        )
        conn.commit(); conn.close()

    # ── FILE LOG ──────────────────────────────────────────────

    def log_file_operation(self, operation: str, file_path: str,
                           destination: str = None,
                           success: bool = True):
        conn = self._conn()
        conn.execute(
            '''INSERT INTO file_log
               (operation,file_path,destination,success)
               VALUES (?,?,?,?)''',
            (operation, file_path, destination, int(success))
        )
        conn.commit(); conn.close()

    # ── SETTINGS ──────────────────────────────────────────────

    def get_setting(self, key: str, default=None):
        conn = self._conn()
        row  = conn.execute(
            'SELECT value FROM settings WHERE key=?', (key,)
        ).fetchone()
        conn.close()
        if row:
            try:    return json.loads(row['value'])
            except: return row['value']
        return default

    def set_setting(self, key: str, value):
        conn = self._conn()
        conn.execute(
            '''INSERT OR REPLACE INTO settings (key,value,updated_at)
               VALUES (?,?,?)''',
            (key, json.dumps(value), datetime.now().isoformat())
        )
        conn.commit(); conn.close()

    # ── STATS ─────────────────────────────────────────────────

    def get_stats(self) -> dict:
        conn = self._conn()
        wa_count = 0
        try:
            wa_count = conn.execute(
                'SELECT COUNT(*) FROM whatsapp_log'
            ).fetchone()[0]
        except Exception:
            pass
        stats = {
            "total_conversations": conn.execute(
                'SELECT COUNT(*) FROM conversations').fetchone()[0],
            "total_contacts": conn.execute(
                'SELECT COUNT(*) FROM contacts').fetchone()[0],
            "emails_sent": conn.execute(
                'SELECT COUNT(*) FROM email_log').fetchone()[0],
            "whatsapp_sent": wa_count,
            "pending_tasks": conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE status='pending'"
            ).fetchone()[0],
        }
        conn.close()
        return stats
