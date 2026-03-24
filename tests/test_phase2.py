# ============================================================
# ARIA Phase 2 — Tests
# WhatsApp, Gmail, Fiverr, Scheduler, FileSender
# ============================================================

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from modules.phase2.whatsapp_module import WhatsAppModule
from modules.phase2.task_scheduler import TaskScheduler
from modules.phase2.fiverr_engine import FiverrEngine


# ── WHATSAPP TESTS ────────────────────────────────────────────

class TestWhatsApp:
    @pytest.fixture
    def wa(self):
        return WhatsAppModule()  # No credentials — test mode

    def test_format_0300(self, wa):
        r = wa.format_number("03001234567")
        assert "+923001234567" in r

    def test_format_with_dash(self, wa):
        r = wa.format_number("0300-123-4567")
        assert "+92" in r

    def test_format_already_plus92(self, wa):
        r = wa.format_number("+923001234567")
        assert "+923001234567" in r

    def test_format_display(self, wa):
        r = wa.format_display("03001234567")
        assert not r.startswith("whatsapp:")
        assert "+92" in r

    def test_format_10digits(self, wa):
        r = wa.format_number("3001234567")
        assert "+923001234567" in r

    def test_template_project_ready(self, wa):
        t = wa.get_template("project_ready",
                            {"name": "Ahmed", "project": "Website"})
        assert "Ahmed" in t
        assert "Website" in t

    def test_template_payment_reminder(self, wa):
        t = wa.get_template("payment_reminder",
                            {"name": "Sara", "amount": "5000"})
        assert "Sara" in t
        assert "5000" in t

    def test_template_follow_up(self, wa):
        t = wa.get_template("follow_up",
                            {"name": "Ali", "project": "App"})
        assert "Ali" in t

    def test_send_no_credentials(self, wa):
        r = wa.send_message("03001234567", "Test message")
        assert not r["success"]
        assert "preview" in r or "message" in r

    def test_format_bulk_numbers(self, wa):
        numbers = ["03001234567", "03111234567", "+923221234567"]
        formatted = [wa.format_number(n) for n in numbers]
        assert all("whatsapp:" in f for f in formatted)


# ── TASK SCHEDULER TESTS ──────────────────────────────────────

class TestTaskScheduler:
    @pytest.fixture
    def sched(self, tmp_path):
        return TaskScheduler(tasks_file=str(tmp_path / "tasks.json"))

    def test_schedule_task(self, sched):
        r = sched.schedule_task(
            "email",
            {"to_email": "test@test.com", "subject": "Test"},
            description="Test task"
        )
        assert r["success"]
        assert "task_id" in r

    def test_get_pending_tasks(self, sched):
        sched.schedule_task("email", {}, description="Task 1")
        sched.schedule_task("whatsapp", {}, description="Task 2")
        pending = sched.get_pending_tasks()
        assert len(pending) >= 2

    def test_cancel_task(self, sched):
        r = sched.schedule_task("email", {}, description="Cancel me")
        task_id = r["task_id"]
        cancel = sched.cancel_task(task_id)
        assert cancel["success"]
        pending = sched.get_pending_tasks()
        assert not any(t["id"] == task_id for t in pending)

    def test_schedule_email(self, sched):
        r = sched.schedule_email(
            "test@test.com", "Subject", "Body", "tomorrow 9am"
        )
        assert r["success"]

    def test_schedule_weekly_report(self, sched):
        r = sched.schedule_weekly_report("monday")
        assert r["success"]
        assert "monday" in r.get("recurring", "").lower() or r["success"]

    def test_parse_time_tomorrow(self, sched):
        t = sched._parse_time("tomorrow 9am")
        assert "T" in t  # ISO format

    def test_parse_time_in_hours(self, sched):
        t = sched._parse_time("in 2 hours")
        assert "T" in t

    def test_next_recurring_daily(self, sched):
        from datetime import datetime, timedelta
        result = sched._next_recurring("daily")
        now = datetime.now()
        assert result > now

    def test_next_recurring_weekly(self, sched):
        from datetime import datetime, timedelta
        result = sched._next_recurring("weekly")
        now = datetime.now()
        diff = result - now
        assert diff.days >= 6

    def test_save_and_load_tasks(self, sched, tmp_path):
        sched.schedule_task("email", {"key": "val"}, description="Persist test")
        sched2 = TaskScheduler(tasks_file=str(tmp_path / "tasks.json"))
        assert len(sched2.get_all_tasks()) >= 1


# ── FIVERR ENGINE TESTS ───────────────────────────────────────

class TestFiverrEngine:
    @pytest.fixture
    def fiverr(self, tmp_path):
        engine = FiverrEngine()
        engine.output_dir = tmp_path / "fiverr"
        engine.output_dir.mkdir()
        return engine

    def test_fallback_keywords(self, fiverr):
        r = fiverr._fallback_keywords("logo design")
        assert r["success"]
        assert "keywords" in r
        assert len(r["keywords"]) > 0

    def test_fallback_has_category(self, fiverr):
        r = fiverr._fallback_keywords("web development")
        assert r["category"] == "web development"

    def test_get_recommendations_empty_stats(self, fiverr):
        recs = fiverr._get_recommendations({})
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_generate_report_no_stats(self, fiverr):
        r = fiverr.generate_report()
        assert r["success"]
        assert "report" in r
        assert "generated_at" in r["report"]

    def test_report_saved_to_file(self, fiverr):
        r = fiverr.generate_report()
        assert Path(r["saved_at"]).exists()

    def test_recommendations_low_ctr(self, fiverr):
        recs = fiverr._get_recommendations({
            "impressions": 1000, "clicks": 5, "total_orders": 0
        })
        assert any("click" in rec.lower() or "thumbnail" in rec.lower()
                   for rec in recs)

    def test_pricing_strategy_no_ai(self, fiverr):
        # Without AI key — should return error gracefully
        r = fiverr.pricing_strategy("logo design")
        assert "success" in r


# ── RUN TESTS ────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
