# ============================================================
# ARIA Phase 3 — Integration Tests
# CV Manager, Job Hunter, SMM, Website, Client Manager
# ============================================================

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from modules.phase3.cv_manager import CVManager
from modules.phase3.job_hunter import JobHunter
from modules.phase3.social_media_manager import SocialMediaManager
from modules.phase3.website_manager import WebsiteManager
from modules.phase3.client_manager import ClientManager
from modules.phase3.opportunity_finder import OpportunityFinder

class TestCVManager:
    @pytest.fixture
    def cv(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        return CVManager(data_dir=str(d))

    def test_cv_init(self, cv):
        assert cv.data_dir.exists()

    def test_build_cv_fallback(self, cv):
        # AI missing should return failure but handle gracefully
        r = cv.build_cv_from_scratch({"name": "Ahmed Ali"})
        assert "success" in r

class TestJobHunter:
    @pytest.fixture
    def jobs(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        return JobHunter(data_dir=str(d))

    def test_jobs_init(self, jobs):
        assert jobs.db_path is not None

    def test_search_jobs_fallback(self, jobs):
        # Should return at least rozee jobs if web available or empty list
        r = jobs.search_jobs("React Developer", location="Lahore")
        assert r["success"]
        assert isinstance(r["jobs"], list)

class TestSocialMedia:
    @pytest.fixture
    def social(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        return SocialMediaManager(data_dir=str(d))

    def test_caption_fallback(self, social):
        r = social.write_caption("Computer Science", "linkedin")
        assert r["success"]
        assert "caption" in r
        assert len(r["caption"]) > 10

class TestWebsiteManager:
    @pytest.fixture
    def web(self, tmp_path):
        d = tmp_path / "site"
        d.mkdir()
        return WebsiteManager(website_path=str(d))

    def test_seo_calculation(self, web):
        # AI missing might return success=False but check handles it
        r = web.check_seo_score("Expert Python developer in Pakistan", "python")
        if r["success"]:
            assert r["overall_score"] > 0
        else:
            assert "message" in r

class TestClientManager:
    @pytest.fixture
    def client(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        return ClientManager(data_dir=str(d))

    def test_client_workflow(self, client):
        # Add client
        r = client.add_client("Test Client", "test@client.com", company="Web Dev project")
        assert r["success"]
        cid = r["client_id"]
        
        # Get client
        c = client._clients.get(cid)
        assert c["name"] == "Test Client"
        
        # Add project
        r2 = client.add_project("Test Client", "Website", 1000, "2026-05-01")
        assert r2["success"]
        assert len(c["projects"]) == 1

class TestOpportunityFinder:
    @pytest.fixture
    def opt(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        return OpportunityFinder(data_dir=str(d))

    def test_opt_init(self, opt):
        assert opt is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
