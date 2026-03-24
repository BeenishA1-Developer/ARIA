# ============================================================
# ARIA Phase 2 — Task Scheduler
# Background tasks, recurring jobs, retry system
# ============================================================

import os
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False


class TaskScheduler:
    """
    ARIA Phase 2 — Task Scheduler.
    - "Kal subah 9 baje Ahmed ko email karo" → scheduled
    - "Har Monday fiverr report banao" → weekly recurring
    - Background mein run karta hai
    - ARIA band ho to bhi tasks queue mein rehte hain
    - Retry system — fail ho to dobara try karo
    """

    def __init__(self, tasks_file: str = "data/scheduled_tasks.json"):
        self.tasks_file = Path(tasks_file)
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: list = []
        self._running = False
        self._thread  = None
        self._load_tasks()
        logger.info("Task Scheduler initialized")

    # ── LOAD / SAVE ───────────────────────────────────────────

    def _load_tasks(self):
        """Saved tasks load karo."""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file) as f:
                    self._tasks = json.load(f)
                logger.info(f"Tasks loaded: {len(self._tasks)}")
            except Exception as e:
                logger.error(f"Load tasks error: {e}")
                self._tasks = []

    def _save_tasks(self):
        """Tasks file mein save karo."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self._tasks, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save tasks error: {e}")

    # ── SCHEDULE TASK ─────────────────────────────────────────

    def schedule_task(self, task_type: str, task_data: dict,
                      run_at: str = None, recurring: str = None,
                      description: str = "") -> dict:
        """
        Task schedule karo.

        task_type:  'email', 'whatsapp', 'fiverr_report', 'file_backup'
        task_data:  Task ke liye data (recipient, message, etc.)
        run_at:     "2024-12-25 09:00" ya "tomorrow 9am"
        recurring:  'daily', 'weekly', 'monday', 'every_hour'
        description: Human-readable description
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._tasks)}"

        # Run time parse karo
        scheduled_time = self._parse_time(run_at) if run_at else None

        task = {
            "id":             task_id,
            "type":           task_type,
            "data":           task_data,
            "description":    description,
            "scheduled_time": scheduled_time,
            "recurring":      recurring,
            "status":         "pending",
            "retry_count":    0,
            "max_retries":    3,
            "created_at":     datetime.now().isoformat(),
            "last_run":       None,
            "next_run":       scheduled_time,
        }

        self._tasks.append(task)
        self._save_tasks()

        logger.success(f"Task scheduled: {task_id} — {description}")
        return {
            "success":     True,
            "task_id":     task_id,
            "description": description,
            "scheduled":   scheduled_time or "immediate",
            "recurring":   recurring,
            "message":     f"Task schedule ho gaya! ID: {task_id}",
        }

    # ── SCHEDULE EMAIL ────────────────────────────────────────

    def schedule_email(self, recipient: str, subject: str,
                       body: str, run_at: str,
                       recurring: str = None) -> dict:
        """Email schedule karo."""
        return self.schedule_task(
            task_type="email",
            task_data={
                "recipient": recipient,
                "subject":   subject,
                "body":      body,
            },
            run_at=run_at,
            recurring=recurring,
            description=f"Email to {recipient}: {subject}",
        )

    # ── SCHEDULE WHATSAPP ─────────────────────────────────────

    def schedule_whatsapp(self, number: str, message: str,
                          run_at: str, recurring: str = None) -> dict:
        """WhatsApp message schedule karo."""
        return self.schedule_task(
            task_type="whatsapp",
            task_data={"number": number, "message": message},
            run_at=run_at,
            recurring=recurring,
            description=f"WhatsApp to {number}",
        )

    # ── SCHEDULE FIVERR REPORT ────────────────────────────────

    def schedule_weekly_report(self, day: str = "monday") -> dict:
        """Har hafta Fiverr report."""
        return self.schedule_task(
            task_type="fiverr_report",
            task_data={"report_type": "weekly"},
            recurring=day,
            description=f"Weekly Fiverr Report — every {day}",
        )

    # ── GET TASKS ─────────────────────────────────────────────

    def get_pending_tasks(self) -> list:
        """Pending tasks lo."""
        return [t for t in self._tasks if t["status"] == "pending"]

    def get_all_tasks(self) -> list:
        """Sab tasks lo."""
        return self._tasks

    def cancel_task(self, task_id: str) -> dict:
        """Task cancel karo."""
        for task in self._tasks:
            if task["id"] == task_id:
                task["status"] = "cancelled"
                self._save_tasks()
                logger.info(f"Task cancelled: {task_id}")
                return {"success": True,
                        "message": f"Task cancel ho gaya: {task_id}"}
        return {"success": False, "message": "Task nahi mila"}

    # ── RUN DUE TASKS ─────────────────────────────────────────

    def check_and_run_due_tasks(self, executors: dict = None) -> list:
        """
        Due tasks check karo aur execute karo.
        executors: {"email": email_fn, "whatsapp": wa_fn, ...}
        """
        now      = datetime.now()
        ran      = []
        executors = executors or {}

        for task in self._tasks:
            if task["status"] != "pending":
                continue

            # Time check
            if task.get("next_run"):
                try:
                    next_run = datetime.fromisoformat(task["next_run"])
                    if now < next_run:
                        continue
                except Exception:
                    pass

            # Execute
            success = self._execute_task(task, executors)
            task["last_run"] = now.isoformat()

            if success:
                task["retry_count"] = 0
                if task.get("recurring"):
                    task["next_run"] = self._next_recurring(
                        task["recurring"]
                    ).isoformat()
                    logger.info(
                        f"Recurring task rescheduled: {task['next_run']}"
                    )
                else:
                    task["status"] = "completed"
                ran.append({"task_id": task["id"], "success": True})
            else:
                task["retry_count"] = task.get("retry_count", 0) + 1
                if task["retry_count"] >= task.get("max_retries", 3):
                    task["status"] = "failed"
                    logger.error(
                        f"Task permanently failed: {task['id']}"
                    )
                ran.append({"task_id": task["id"], "success": False})

        if ran:
            self._save_tasks()

        return ran

    def _execute_task(self, task: dict, executors: dict) -> bool:
        """Single task execute karo."""
        task_type = task.get("type")
        data      = task.get("data", {})
        executor  = executors.get(task_type)

        if executor:
            try:
                result = executor(data)
                return result.get("success", False) if isinstance(result, dict) else bool(result)
            except Exception as e:
                logger.error(f"Task execution error: {task['id']} — {e}")
                return False

        # Default: just log
        logger.info(
            f"Task due (no executor): {task['id']} — {task.get('description')}"
        )
        return True  # Mark as done even without executor

    # ── TIME PARSING ──────────────────────────────────────────

    def _parse_time(self, time_str: str) -> str:
        """Natural language time parse karo."""
        now = datetime.now()
        ts  = time_str.lower().strip()

        # "tomorrow 9am" / "kal 9 baje"
        if any(w in ts for w in ["tomorrow", "kal"]):
            base = now + timedelta(days=1)
            hour = self._extract_hour(ts)
            return base.replace(
                hour=hour, minute=0, second=0, microsecond=0
            ).isoformat()

        # "in 2 hours" / "2 ghante baad"
        m = __import__('re').search(r'in (\d+) hour', ts)
        if m:
            return (now + timedelta(hours=int(m.group(1)))).isoformat()

        # "2024-12-25 09:00"
        for fmt in ["%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d"]:
            try:
                return datetime.strptime(time_str, fmt).isoformat()
            except ValueError:
                pass

        # Today at given hour
        hour = self._extract_hour(ts)
        scheduled = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if scheduled <= now:
            scheduled += timedelta(days=1)
        return scheduled.isoformat()

    def _extract_hour(self, text: str) -> int:
        """Time se hour extract karo."""
        import re
        # "9am", "9 am", "9:00", "9 baje"
        m = re.search(r'(\d{1,2})\s*(?:am|pm|:00|baje)', text)
        if m:
            h = int(m.group(1))
            if 'pm' in text and h < 12:
                h += 12
            return max(0, min(23, h))
        return 9  # Default: 9am

    def _next_recurring(self, recurring: str) -> datetime:
        """Agle recurring time calculate karo."""
        now  = datetime.now()
        days = {
            "monday":    0, "tuesday": 1, "wednesday": 2,
            "thursday":  3, "friday":  4, "saturday":  5, "sunday": 6,
        }
        r = recurring.lower()

        if r == "daily":
            return now + timedelta(days=1)
        elif r == "every_hour":
            return now + timedelta(hours=1)
        elif r == "weekly":
            return now + timedelta(weeks=1)
        elif r in days:
            target = days[r]
            delta  = (target - now.weekday()) % 7
            if delta == 0:
                delta = 7
            return now + timedelta(days=delta)

        return now + timedelta(days=7)

    # ── BACKGROUND RUNNER ─────────────────────────────────────

    def start_background(self, executors: dict = None,
                         check_interval: int = 60):
        """Background thread mein tasks check karo."""
        if self._running:
            return

        self._running = True

        def _run():
            logger.info(
                f"Task Scheduler background running "
                f"(check every {check_interval}s)"
            )
            while self._running:
                try:
                    self.check_and_run_due_tasks(executors)
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                time.sleep(check_interval)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.success("Task Scheduler started in background!")

    def stop_background(self):
        """Background scheduler band karo."""
        self._running = False
        logger.info("Task Scheduler stopped")
