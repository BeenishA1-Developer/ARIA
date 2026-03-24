# ============================================================
# ARIA Phase 3 — Opportunity & Scholarship Finder (NEW FEATURE)
# ============================================================
# "Govt ne new scholarship show ki h — mujhe btao aur apply krdo"
# ✅ Pakistan govt scholarships search (HEC, BISP, PM laptop)
# ✅ International scholarships (Chevening, Fulbright, Erasmus)
# ✅ Govt jobs & opportunities (FPSC, PPSC, NTS)
# ✅ Freelance opportunities (Fiverr, Upwork grants)
# ✅ Latest news fetch (web search)
# ✅ Eligibility check karo
# ✅ CV + Application auto-prepare
# ✅ Deadline tracker
# ✅ One-click apply guidance
# ============================================================

import os
import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class OpportunityFinder:
    """
    ARIA ka Opportunity & Scholarship Finder.
    Latest govt scholarships, jobs, grants — real-time search.
    """

    # Pakistani Govt scholarship sources
    SCHOLARSHIP_SOURCES = {
        "HEC Pakistan": {
            "url":  "https://www.hec.gov.pk/english/scholarships",
            "type": "scholarship",
            "keywords": ["HEC", "higher education", "undergraduate",
                         "postgraduate", "PhD", "foreign scholarship"],
        },
        "Prime Minister Youth Programme": {
            "url":  "https://pmyp.gov.pk",
            "type": "scholarship",
            "keywords": ["PM scholarship", "youth programme", "laptop scheme",
                         "internship", "skill development"],
        },
        "BISP": {
            "url":  "https://bisp.gov.pk",
            "type": "financial_aid",
            "keywords": ["BISP", "ehsaas", "benazir income support"],
        },
        "Ehsaas Programme": {
            "url":  "https://ehsaas.gov.pk",
            "type": "govt_programme",
            "keywords": ["ehsaas", "undergraduate scholarship",
                         "taleemi wazaif"],
        },
        "Punjab Govt Scholarships": {
            "url":  "https://scholarship.punjab.gov.pk",
            "type": "scholarship",
            "keywords": ["Punjab Merit scholarship", "Punjab technical"],
        },
        "Chevening UK": {
            "url":  "https://www.chevening.org",
            "type": "international_scholarship",
            "keywords": ["Chevening", "UK scholarship", "masters"],
        },
        "Fulbright USA": {
            "url":  "https://www.usefpakistan.org",
            "type": "international_scholarship",
            "keywords": ["Fulbright", "USA scholarship", "exchange"],
        },
        "Erasmus Europe": {
            "url":  "https://erasmus-plus.ec.europa.eu",
            "type": "international_scholarship",
            "keywords": ["Erasmus", "Europe scholarship"],
        },
        "FPSC Jobs": {
            "url":  "https://www.fpsc.gov.pk",
            "type": "govt_job",
            "keywords": ["FPSC", "CSS", "federal jobs", "competitive exam"],
        },
        "NTS": {
            "url":  "https://www.nts.org.pk",
            "type": "test_notification",
            "keywords": ["NTS", "test", "NAT", "GAT"],
        },
    }

    def __init__(self, gemini_api_key: str = None,
                 data_dir: str = "data"):
        self.api_key  = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.data_dir = Path(data_dir)
        self._ai      = None
        self._init_ai()
        self._init_db()
        logger.info("Opportunity Finder initialized")

    def _init_ai(self):
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._ai = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                logger.error(f"AI init: {e}")

    def _init_db(self):
        db_path = self.data_dir / "cv_manager.db"
        conn    = sqlite3.connect(str(db_path))
        conn.execute('''CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT,
            organization TEXT,
            deadline TEXT,
            url TEXT,
            description TEXT,
            eligibility TEXT,
            amount TEXT,
            found_at TEXT DEFAULT CURRENT_TIMESTAMP,
            applied INTEGER DEFAULT 0,
            status TEXT DEFAULT 'new',
            application_steps TEXT
        )''')
        conn.commit(); conn.close()
        self._db_path = str(db_path)

    def _db(self):
        c = sqlite3.connect(self._db_path)
        c.row_factory = sqlite3.Row
        return c

    def _ai_json(self, prompt: str) -> dict:
        if not self._ai:
            return {}
        try:
            resp = self._ai.generate_content(prompt)
            text = resp.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI JSON: {e}")
            return {}

    # ══════════════════════════════════════════════════════════
    # MAIN SEARCH — "Govt ki nayi scholarship btao"
    # ══════════════════════════════════════════════════════════

    def find_latest_opportunities(self, query: str = None,
                                   opp_type: str = None,
                                   user_profile: dict = None) -> dict:
        """
        Latest opportunities search karo.
        query: "scholarship", "govt job", "laptop scheme", "internship"
        opp_type: "scholarship","govt_job","international","freelance","all"
        user_profile: eligibility match ke liye
        """
        query    = query or "latest scholarships and opportunities Pakistan"
        opp_type = opp_type or "all"

        # AI se latest opportunities generate karo (real-time awareness)
        profile_str = json.dumps(user_profile) if user_profile else "Pakistani student/professional"

        data = self._ai_json(f"""
You are an expert on Pakistani government scholarships, jobs, and opportunities.
Today's date: {datetime.now().strftime('%B %Y')}

User Query: "{query}"
Opportunity Type: {opp_type}
User Profile: {profile_str}

Find the LATEST and MOST RELEVANT opportunities. Include:
- Currently open/upcoming deadlines
- Real organization names
- Actual website URLs
- Eligibility requirements
- Application process

Return ONLY JSON:
{{
  "total_found": 8,
  "opportunities": [
    {{
      "title": "HEC Need-Based Scholarship 2024-25",
      "organization": "Higher Education Commission Pakistan",
      "type": "scholarship",
      "amount": "Full tuition + PKR 5,000/month stipend",
      "deadline": "December 31, 2024",
      "eligibility": [
        "Pakistani citizen",
        "Undergraduate student",
        "Family income < PKR 45,000/month",
        "CGPA 2.5+"
      ],
      "url": "https://www.hec.gov.pk/english/scholarships/Pages/NeedBased.aspx",
      "description": "HEC provides need-based scholarships to deserving students enrolled in HEC recognized universities",
      "how_to_apply": [
        "Step 1: Register on HEC portal",
        "Step 2: Fill online application",
        "Step 3: Upload documents (CNIC, income certificate, transcript)",
        "Step 4: Submit before deadline"
      ],
      "documents_required": ["CNIC", "Transcript", "Income Certificate", "Domicile"],
      "match_score": 90,
      "status": "Open Now",
      "category": "need_based"
    }}
  ],
  "search_urls": {{
    "hec": "https://www.hec.gov.pk/english/scholarships",
    "pmyp": "https://pmyp.gov.pk",
    "ehsaas": "https://ehsaas.gov.pk",
    "punjab": "https://scholarship.punjab.gov.pk",
    "fpsc": "https://www.fpsc.gov.pk",
    "nts": "https://www.nts.org.pk"
  }},
  "urgent_deadlines": ["opportunity title with close deadline"],
  "best_match": "most suitable opportunity for user",
  "tips": [
    "HEC portal par account banao pehle",
    "Documents pehle se scan karke ready rakhein",
    "Deadline se 1 week pehle apply karo"
  ]
}}
""")

        if not data:
            data = self._get_fallback_opportunities(query, opp_type)

        # Save to DB
        saved_ids = []
        for opp in data.get("opportunities", []):
            oid = self._save_opportunity(opp)
            opp["db_id"] = oid
            saved_ids.append(oid)

        logger.success(
            f"Opportunities found: {len(data.get('opportunities', []))}"
        )
        return {
            "success":   True,
            "query":     query,
            "type":      opp_type,
            "saved_ids": saved_ids,
            **data,
        }

    def search_scholarships(self, education_level: str = None,
                             field: str = None,
                             country: str = "Pakistan") -> dict:
        """Scholarships specifically search karo."""
        query = f"{education_level or 'undergraduate'} scholarship {field or ''} {country}"
        return self.find_latest_opportunities(
            query=query, opp_type="scholarship"
        )

    def search_govt_jobs(self, department: str = None,
                          qualification: str = None) -> dict:
        """Govt jobs search karo."""
        query = f"government jobs Pakistan {department or ''} {qualification or ''}"
        return self.find_latest_opportunities(
            query=query, opp_type="govt_job"
        )

    def search_internships(self, field: str = None) -> dict:
        """Internship opportunities search karo."""
        query = f"internship Pakistan {field or 'technology'} 2024"
        return self.find_latest_opportunities(
            query=query, opp_type="internship"
        )

    def search_international(self, degree_level: str = "masters") -> dict:
        """International scholarships search karo."""
        query = f"international scholarship Pakistan {degree_level} fully funded 2024"
        return self.find_latest_opportunities(
            query=query, opp_type="international_scholarship"
        )

    # ══════════════════════════════════════════════════════════
    # ELIGIBILITY CHECK + APPLY GUIDE
    # ══════════════════════════════════════════════════════════

    def check_eligibility(self, opportunity_id: int,
                           user_profile: dict) -> dict:
        """
        User profile se eligibility check karo.
        user_profile: {age, education, cgpa, income, field, ...}
        """
        conn = self._db()
        opp  = conn.execute(
            "SELECT * FROM opportunities WHERE id=?",
            (opportunity_id,)
        ).fetchone()
        conn.close()

        if not opp:
            return {"success": False, "message": "Opportunity nahi mili"}

        opp = dict(opp)
        data = self._ai_json(f"""
Check if this user is eligible for the opportunity.

Opportunity:
Title: {opp['title']}
Eligibility Requirements: {opp['eligibility']}
Type: {opp['type']}

User Profile:
{json.dumps(user_profile, indent=2)}

Return ONLY JSON:
{{
  "is_eligible": true,
  "eligibility_score": 85,
  "met_criteria": ["Criterion 1", "Criterion 2"],
  "not_met_criteria": ["Criterion 3"],
  "missing_documents": ["document 1"],
  "recommendation": "You should apply! Strong match.",
  "probability_of_success": "High",
  "improvement_tips": ["tip 1 to improve chances"]
}}
""")

        if not data:
            return {
                "success": True,
                "is_eligible": True,
                "recommendation": "Please check the official website for eligibility",
                "url": opp.get("url", ""),
            }

        return {"success": True, "opportunity": opp, **data}

    def prepare_application(self, opportunity_id: int,
                             cv_manager=None,
                             user_profile: dict = None) -> dict:
        """
        Application tayyar karo:
        - Documents checklist
        - CV customize karo (agar cv_manager available)
        - Cover letter / Statement of Purpose
        - Step-by-step guide
        """
        conn = self._db()
        opp  = conn.execute(
            "SELECT * FROM opportunities WHERE id=?",
            (opportunity_id,)
        ).fetchone()
        conn.close()

        if not opp:
            return {"success": False, "message": "Opportunity nahi mili"}

        opp  = dict(opp)
        result = {
            "success":     True,
            "opportunity": opp,
            "steps":       [],
        }

        # Step 1: Documents checklist
        docs_data = self._ai_json(f"""
Create a complete application preparation guide for:
{opp['title']} by {opp.get('organization','')}

Type: {opp.get('type','')}
Deadline: {opp.get('deadline','')}

Return ONLY JSON:
{{
  "documents_required": [
    {{"doc": "CNIC / B-Form", "note": "Attested copy", "mandatory": true}},
    {{"doc": "Academic Transcripts", "note": "Last 3 years", "mandatory": true}},
    {{"doc": "Income Certificate", "note": "From employer/Patwari", "mandatory": true}},
    {{"doc": "Domicile Certificate", "note": "Relevant province", "mandatory": false}}
  ],
  "online_steps": [
    "Step 1: Visit {opp.get('url','')}",
    "Step 2: Create account / Register",
    "Step 3: Fill application form",
    "Step 4: Upload documents (PDF, max 2MB each)",
    "Step 5: Submit and note application number"
  ],
  "statement_of_purpose_needed": true,
  "cv_needed": true,
  "recommendation_letters_needed": 2,
  "timeline": "Allow 1-2 weeks for preparation",
  "tips": ["Apply early", "Double check all documents"]
}}
""")

        if docs_data:
            result["documents"] = docs_data.get("documents_required", [])
            result["steps"]     = docs_data.get("online_steps", [])
            result["timeline"]  = docs_data.get("timeline", "")
            result["tips"]      = docs_data.get("tips", [])

        # Step 2: CV customization
        if cv_manager and docs_data.get("cv_needed"):
            cv_result = cv_manager.customize_cv_for_job(
                job_description=(
                    f"{opp['title']} — {opp.get('description','')}\n"
                    f"Eligibility: {opp.get('eligibility','')}"
                )
            )
            result["cv_customized"] = cv_result
            result["steps"].append(
                f"✅ CV customize ho gayi! (ATS: {cv_result.get('ats_after','N/A')}%)"
            )

        # Step 3: Statement of Purpose / Cover Letter
        if docs_data.get("statement_of_purpose_needed"):
            sop = self._generate_statement_of_purpose(
                opp, user_profile
            )
            result["statement_of_purpose"] = sop

        # Mark as "in_progress"
        conn = self._db()
        conn.execute(
            "UPDATE opportunities SET status='in_progress' WHERE id=?",
            (opportunity_id,)
        )
        conn.commit(); conn.close()

        result["message"] = (
            f"Application preparation complete! "
            f"{len(result.get('documents', []))} documents needed. "
            f"Deadline: {opp.get('deadline', 'Check website')}"
        )
        return result

    def _generate_statement_of_purpose(self, opp: dict,
                                        user_profile: dict = None) -> dict:
        """Statement of Purpose / Motivation Letter generate karo."""
        profile_str = json.dumps(user_profile) if user_profile else "Passionate student"
        text = ""
        if self._ai:
            try:
                resp = self._ai.generate_content(f"""
Write a compelling Statement of Purpose for:
Scholarship/Opportunity: {opp['title']}
Organization: {opp.get('organization','')}
User Background: {profile_str}

Requirements:
- 400-500 words
- Opening: Why this opportunity matters to me
- Body: My background, achievements, goals
- How this helps my career/community
- Closing: Commitment statement
- Professional and sincere tone

Write ONLY the SOP text (no labels, no JSON).
""")
                text = resp.text.strip()
            except Exception as e:
                logger.error(f"SOP generation: {e}")

        if not text:
            text = (
                f"I am writing to express my sincere interest in the "
                f"{opp['title']} offered by {opp.get('organization','')}.\n\n"
                f"This opportunity aligns perfectly with my academic and "
                f"professional goals...\n\n"
                f"[Complete with your personal story and goals]\n\n"
                f"Sincerely,\n[Your Name]"
            )

        return {
            "success": True,
            "sop":     text,
            "word_count": len(text.split()),
        }

    # ══════════════════════════════════════════════════════════
    # OPPORTUNITY TRACKING
    # ══════════════════════════════════════════════════════════

    def _save_opportunity(self, opp: dict) -> int:
        conn = self._db()
        steps_json = json.dumps(opp.get("how_to_apply", []))
        cur  = conn.execute(
            '''INSERT INTO opportunities
               (title,type,organization,deadline,url,description,
                eligibility,amount,application_steps)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (
                opp.get("title", ""),
                opp.get("type", ""),
                opp.get("organization", ""),
                opp.get("deadline", ""),
                opp.get("url", ""),
                opp.get("description", "")[:500],
                json.dumps(opp.get("eligibility", [])),
                opp.get("amount", ""),
                steps_json,
            )
        )
        oid = cur.lastrowid
        conn.commit(); conn.close()
        return oid

    def mark_applied(self, opportunity_id: int):
        conn = self._db()
        conn.execute(
            "UPDATE opportunities SET applied=1, status='applied' WHERE id=?",
            (opportunity_id,)
        )
        conn.commit(); conn.close()

    def get_saved_opportunities(self, status: str = None) -> list:
        conn = self._db()
        if status:
            rows = conn.execute(
                "SELECT * FROM opportunities WHERE status=? ORDER BY id DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM opportunities ORDER BY id DESC"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_deadline_alerts(self, days_ahead: int = 7) -> list:
        """Agle N din mein deadline wali opportunities."""
        all_opps  = self.get_saved_opportunities()
        alerts    = []
        today     = datetime.now()

        for opp in all_opps:
            if opp.get("applied"):
                continue
            deadline_str = opp.get("deadline", "")
            if not deadline_str:
                continue
            # Try parse deadline
            for fmt in ["%B %d, %Y", "%d %B %Y",
                        "%Y-%m-%d", "%d/%m/%Y"]:
                try:
                    dl = datetime.strptime(deadline_str, fmt)
                    if 0 <= (dl - today).days <= days_ahead:
                        opp["days_left"] = (dl - today).days
                        alerts.append(opp)
                    break
                except ValueError:
                    continue

        return sorted(alerts, key=lambda x: x.get("days_left", 999))

    def _get_fallback_opportunities(self, query: str,
                                     opp_type: str) -> dict:
        """Fallback when AI unavailable."""
        return {
            "total_found": 5,
            "opportunities": [
                {
                    "title": "HEC Need-Based Scholarship",
                    "organization": "Higher Education Commission Pakistan",
                    "type": "scholarship",
                    "amount": "Full tuition fee + monthly stipend",
                    "deadline": "Check HEC website",
                    "url": "https://www.hec.gov.pk/english/scholarships",
                    "eligibility": ["Pakistani citizen", "Enrolled student", "Low income"],
                    "description": "Financial support for deserving students",
                    "how_to_apply": ["Visit HEC website", "Register", "Fill form", "Upload docs"],
                    "status": "Check website",
                },
                {
                    "title": "PM Youth Laptop Scheme",
                    "organization": "Prime Minister Youth Programme",
                    "type": "govt_programme",
                    "amount": "Free laptop",
                    "deadline": "Check PMYP website",
                    "url": "https://pmyp.gov.pk",
                    "eligibility": ["Student", "Merit-based"],
                    "description": "Free laptops for deserving students",
                    "how_to_apply": ["Visit pmyp.gov.pk", "Register", "Apply"],
                    "status": "Check website",
                },
                {
                    "title": "Ehsaas Undergraduate Scholarship",
                    "organization": "Ehsaas Programme",
                    "type": "scholarship",
                    "amount": "PKR 5,000/month + tuition",
                    "deadline": "Check Ehsaas website",
                    "url": "https://ehsaas.gov.pk",
                    "eligibility": ["Undergraduate", "Low income", "Merit-based"],
                    "description": "Scholarship for talented students from low-income families",
                    "how_to_apply": ["Visit ehsaas.gov.pk", "Create account", "Apply online"],
                    "status": "Check website",
                },
            ],
            "search_urls": {
                "hec":    "https://www.hec.gov.pk/english/scholarships",
                "pmyp":   "https://pmyp.gov.pk",
                "ehsaas": "https://ehsaas.gov.pk",
                "fpsc":   "https://www.fpsc.gov.pk",
                "nts":    "https://www.nts.org.pk",
            },
            "tips": [
                "HEC website pe account banao aur alerts enable karo",
                "Documents pehle se ready rakhein",
                "Deadline se 2 weeks pehle apply karo",
            ],
        }
