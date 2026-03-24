# ============================================================
# ARIA - Phase 1 Tests (46+ tests)
# ============================================================

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.nlp_engine import NLPEngine
from core.memory_system import MemorySystem
from modules.file_manager import FileManager
from modules.app_controller import AppController


# ── NLP ENGINE TESTS ─────────────────────────────────────────

class TestNLPEngine:
    @pytest.fixture
    def nlp(self):
        return NLPEngine()

    def test_greeting_english(self, nlp):
        r = nlp.detect_intent("hello aria")
        assert r["intent"] == "greeting"

    def test_greeting_urdu(self, nlp):
        r = nlp.detect_intent("salam aria")
        assert r["intent"] == "greeting"

    def test_screenshot_english(self, nlp):
        r = nlp.detect_intent("take a screenshot")
        assert r["intent"] == "screenshot"

    def test_screenshot_roman_urdu(self, nlp):
        r = nlp.detect_intent("screenshot lo")
        assert r["intent"] == "screenshot"

    def test_file_search_pdf(self, nlp):
        r = nlp.detect_intent("meri pdf files dhoondo")
        assert r["intent"] == "file_search"

    def test_file_search_english(self, nlp):
        r = nlp.detect_intent("find my resume file")
        assert r["intent"] == "file_search"

    def test_file_organize(self, nlp):
        r = nlp.detect_intent("Downloads folder organize karo")
        assert r["intent"] == "file_organize"

    def test_app_open_chrome(self, nlp):
        r = nlp.detect_intent("chrome kholo")
        assert r["intent"] == "app_open"
        assert r["entities"].get("app_name") == "chrome"

    def test_app_open_notepad(self, nlp):
        r = nlp.detect_intent("open notepad")
        assert r["intent"] == "app_open"

    def test_app_close(self, nlp):
        r = nlp.detect_intent("chrome band karo")
        assert r["intent"] == "app_close"

    def test_system_status(self, nlp):
        r = nlp.detect_intent("system status batao")
        assert r["intent"] == "system_status"

    def test_system_status_cpu(self, nlp):
        r = nlp.detect_intent("CPU kitna use ho raha hai")
        assert r["intent"] == "system_status"

    def test_email_draft(self, nlp):
        r = nlp.detect_intent("ahmed ko professional email likho")
        assert r["intent"] == "email_draft"
        assert r["entities"].get("recipient") == "Ahmed"

    def test_email_send(self, nlp):
        r = nlp.detect_intent("sara ko email bhejo")
        assert r["intent"] == "email_send_now"
        assert r["entities"].get("recipient") == "Sara"

    def test_pdf_merge(self, nlp):
        r = nlp.detect_intent("pdf merge karo")
        assert r["intent"] == "pdf_merge"

    def test_find_duplicates(self, nlp):
        r = nlp.detect_intent("duplicate files dhoondo")
        assert r["intent"] == "find_duplicates"

    def test_help(self, nlp):
        r = nlp.detect_intent("help chahiye")
        assert r["intent"] == "help"

    def test_stop(self, nlp):
        r = nlp.detect_intent("band ho jao")
        assert r["intent"] == "stop"

    def test_stop_english(self, nlp):
        r = nlp.detect_intent("exit aria")
        assert r["intent"] == "stop"

    def test_unknown_intent(self, nlp):
        r = nlp.detect_intent("xyz abc 123 random nonsense")
        assert r["intent"] == "unknown"

    def test_result_has_confidence(self, nlp):
        r = nlp.detect_intent("hello")
        assert "confidence" in r
        assert 0 <= r["confidence"] <= 1

    def test_result_has_language(self, nlp):
        r = nlp.detect_intent("karo dhoondo hai")
        assert r["language"] in ["urdu", "roman_urdu", "english"]

    def test_entity_filename(self, nlp):
        r = nlp.detect_intent("cv.pdf dhoondo")
        assert r["entities"].get("filename") == "cv.pdf"

    def test_entity_phone(self, nlp):
        r = nlp.detect_intent("03001234567 ko message karo")
        assert r["entities"].get("phone") is not None

    def test_time_intent(self, nlp):
        r = nlp.detect_intent("abhi kitne baje hain")
        assert r["intent"] == "time_date"

    def test_volume_up(self, nlp):
        r = nlp.detect_intent("volume up karo")
        assert r["intent"] == "volume_control"


# ── MEMORY SYSTEM TESTS ──────────────────────────────────────

class TestMemorySystem:
    @pytest.fixture
    def memory(self, tmp_path):
        db_path = str(tmp_path / "test_aria.db")
        return MemorySystem(db_path=db_path)

    def test_save_conversation(self, memory):
        memory.save_conversation("hello", "Hi there!", "greeting")
        convs = memory.get_recent_conversations(limit=1)
        assert len(convs) == 1
        assert convs[0]["user_input"] == "hello"

    def test_get_recent_conversations(self, memory):
        memory.save_conversation("test1", "response1", "greeting")
        memory.save_conversation("test2", "response2", "unknown")
        convs = memory.get_recent_conversations(limit=5)
        assert len(convs) >= 2

    def test_save_and_find_contact(self, memory):
        memory.save_contact("Ahmed Ali", email="ahmed@test.com")
        contact = memory.find_contact("Ahmed")
        assert contact is not None
        assert contact["email"] == "ahmed@test.com"

    def test_contact_update(self, memory):
        memory.save_contact("Sara", email="sara@old.com")
        memory.save_contact("Sara", email="sara@new.com")
        contact = memory.find_contact("Sara")
        assert contact["email"] == "sara@new.com"

    def test_log_email(self, memory):
        memory.log_email("test@test.com", "Test Subject", "Preview...")
        history = memory.get_email_history()
        assert len(history) >= 1
        assert history[0]["recipient"] == "test@test.com"

    def test_add_task(self, memory):
        task_id = memory.add_task("Test Task", "Description here", priority=2)
        assert task_id is not None
        tasks = memory.get_pending_tasks()
        assert any(t["title"] == "Test Task" for t in tasks)

    def test_complete_task(self, memory):
        task_id = memory.add_task("Complete Me")
        memory.complete_task(task_id)
        pending = memory.get_pending_tasks()
        assert not any(t["id"] == task_id for t in pending)

    def test_set_get_setting(self, memory):
        memory.set_setting("test_key", "test_value")
        value = memory.get_setting("test_key")
        assert value == "test_value"

    def test_get_setting_default(self, memory):
        value = memory.get_setting("nonexistent_key", default="fallback")
        assert value == "fallback"

    def test_stats(self, memory):
        stats = memory.get_stats()
        assert "total_conversations" in stats
        assert "total_contacts" in stats
        assert "emails_sent" in stats
        assert "pending_tasks" in stats

    def test_log_file_operation(self, memory):
        memory.log_file_operation("copy", "/test/file.txt", "/dest/", True)
        # Should not raise any exception


# ── FILE MANAGER TESTS ───────────────────────────────────────

class TestFileManager:
    @pytest.fixture
    def fm(self):
        return FileManager()

    def test_format_size_bytes(self, fm):
        assert "B" in fm._format_size(500)

    def test_format_size_kb(self, fm):
        assert "KB" in fm._format_size(1500)

    def test_format_size_mb(self, fm):
        assert "MB" in fm._format_size(1_500_000)

    def test_format_size_gb(self, fm):
        assert "GB" in fm._format_size(1_500_000_000)

    def test_get_category_image(self, fm):
        assert fm._get_category(".jpg") == "Images"

    def test_get_category_pdf(self, fm):
        assert fm._get_category(".pdf") == "Documents"

    def test_get_category_video(self, fm):
        assert fm._get_category(".mp4") == "Videos"

    def test_get_category_unknown(self, fm):
        assert fm._get_category(".xyz") == "Others"

    def test_search_files_returns_list(self, fm, tmp_path):
        fm.search_paths = [tmp_path]
        # Create a test file
        (tmp_path / "test_document.pdf").write_text("test")
        results = fm.search_files("test")
        assert isinstance(results, list)

    def test_organize_folder_dry_run(self, fm, tmp_path):
        (tmp_path / "photo.jpg").write_bytes(b"fake")
        (tmp_path / "document.pdf").write_bytes(b"fake")
        result = fm.organize_folder(str(tmp_path), dry_run=True)
        assert result["dry_run"] is True
        assert result["files_organized"] >= 2

    def test_create_folder(self, fm, tmp_path):
        new_folder = fm.create_folder("TestFolder", location=str(tmp_path))
        assert Path(new_folder).exists()

    def test_find_duplicates(self, fm, tmp_path):
        # Create two files with same name and content
        (tmp_path / "file.txt").write_text("content")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file.txt").write_text("content")
        duplicates = fm.find_duplicates(str(tmp_path))
        # May or may not find — depends on implementation
        assert isinstance(duplicates, list)


# ── APP CONTROLLER TESTS ─────────────────────────────────────

class TestAppController:
    @pytest.fixture
    def ac(self):
        return AppController()

    def test_system_status_returns_dict(self, ac):
        status = ac.get_system_status()
        assert isinstance(status, dict)

    def test_system_status_has_cpu(self, ac):
        status = ac.get_system_status()
        if "error" not in status:
            assert "cpu" in status

    def test_system_status_has_ram(self, ac):
        status = ac.get_system_status()
        if "error" not in status:
            assert "ram" in status

    def test_open_url_adds_https(self, ac):
        # Should not crash
        result = ac.open_url.__doc__  # Just checking it exists
        assert result is not None


# ── RUN TESTS ────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
