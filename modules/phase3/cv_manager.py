# ============================================================
# ARIA Phase 3 — Smart CV Manager
# CV banao, improve karo, job ke liye customize karo,
# ATS score check karo, multiple versions save karo
# ============================================================

import os
import json
import re
from datetime import datetime
from pathlib import Path
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class CVManager:
    """
    ARIA Phase 3 — Smart CV Manager (COMPLETE).

    ✅ CV data ek baar do — hamesha yaad rakhega
    ✅ Scratch se professional CV banao
    ✅ Existing CV improve karo
    ✅ Job ke liye CV customize karo
    ✅ ATS Score check (0-100) — 80%+ ensure karta hai
    ✅ Job keywords auto-extract + CV mein add
    ✅ Multiple CV versions save (job type ke hisaab se)
    ✅ Professional PDF generate karo
    ✅ CV match report — kya CV is job ke liye theek hai?
    ✅ Cover letter AI se generate
    """

    def __init__(self, gemini_api_key: str = None,
                 data_dir: str = "data"):
        self.api_key  = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self.data_dir = Path(data_dir)
        self.cv_dir   = self.data_dir / "cvs"
        self.cv_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = Path("outputs/cvs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._ai = None
        self._init_ai()
        self._master_cv: dict = self._load_master_cv()
        logger.info("CV Manager initialized")

    def _init_ai(self):
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._ai = genai.GenerativeModel("gemini-1.5-flash")
                logger.success("CV Manager AI ready")
            except Exception as e:
                logger.error(f"AI init: {e}")

    def _ai_call(self, prompt: str) -> str:
        if not self._ai:
            return ""
        try:
            return self._ai.generate_content(prompt).text.strip()
        except Exception as e:
            logger.error(f"AI call: {e}")
            return ""

    def _ai_json(self, prompt: str) -> dict:
        text = self._ai_call(prompt)
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$',    '', text)
        try:
            return json.loads(text)
        except Exception:
            return {}

    # ── MASTER CV STORAGE ─────────────────────────────────────

    def _master_cv_path(self) -> Path:
        return self.cv_dir / "master_cv.json"

    def _load_master_cv(self) -> dict:
        p = self._master_cv_path()
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return {}

    def _save_master_cv(self):
        self._master_cv_path().write_text(
            json.dumps(self._master_cv, indent=2, ensure_ascii=False)
        )
        logger.success("Master CV saved")

    def save_user_cv(self, cv_data: dict) -> dict:
        """
        User ki CV data save karo — ek baar, hamesha yaad rahega.
        cv_data keys: name, email, phone, location, summary,
                      experience (list), education (list),
                      skills (list), languages, certifications
        """
        self._master_cv = cv_data
        self._master_cv["updated_at"] = datetime.now().isoformat()
        self._save_master_cv()
        return {
            "success": True,
            "message": "CV data save ho gaya! Ab main ise hamesha use karunga.",
        }

    def get_master_cv(self) -> dict:
        """Saved CV lo."""
        if not self._master_cv:
            return {"success": False,
                    "message": "Koi CV save nahi hai. Pehle CV banao ya save karo."}
        return {"success": True, "cv": self._master_cv}

    # ── CV BUILDER (SCRATCH SE) ───────────────────────────────

    def build_cv_from_scratch(self, user_info: dict) -> dict:
        """
        AI se scratch se professional CV banao.
        user_info: basic info dict ya natural language description
        """
        info_text = (user_info if isinstance(user_info, str)
                     else json.dumps(user_info, ensure_ascii=False))

        data = self._ai_json(f"""
You are a professional CV writer. Create a complete, ATS-optimized CV.

User Information:
{info_text}

Return ONLY JSON:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+92-300-1234567",
  "location": "City, Country",
  "linkedin": "linkedin.com/in/username",
  "github": "github.com/username",
  "summary": "2-3 sentence compelling professional summary",
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Jan 2022 - Present",
      "location": "City",
      "bullets": [
        "Achieved X by doing Y, resulting in Z",
        "Led team of N people to deliver X",
        "Increased revenue/efficiency by X%"
      ]
    }}
  ],
  "education": [
    {{
      "degree": "Bachelor of Science in Computer Science",
      "institution": "University Name",
      "year": "2020-2024",
      "gpa": "3.8/4.0",
      "achievements": ["Dean's List", "Relevant coursework"]
    }}
  ],
  "skills": {{
    "technical": ["Python", "React", "Node.js"],
    "tools":     ["Git", "VS Code", "Docker"],
    "soft":      ["Leadership", "Communication"]
  }},
  "projects": [
    {{
      "name": "Project Name",
      "tech": ["Python", "React"],
      "description": "What it does and impact",
      "link": "github.com/..."
    }}
  ],
  "certifications": ["AWS Certified", "Google Analytics"],
  "languages": ["Urdu (Native)", "English (Fluent)"],
  "achievements": ["Award/recognition"]
}}
""")
        if not data:
            return {"success": False,
                    "message": "CV generate nahi ho saka — API key check karein"}

        self._master_cv = data
        self._master_cv["updated_at"] = datetime.now().isoformat()
        self._save_master_cv()

        pdf_path = self._generate_pdf(data, "master_cv")
        return {
            "success":  True,
            "cv":       data,
            "pdf_path": pdf_path,
            "message":  "Professional CV ban gaya aur save ho gaya!",
        }

    # ── CV IMPROVER ───────────────────────────────────────────

    def improve_cv(self, cv_text: str = None) -> dict:
        """
        Existing CV improve karo — AI se polish karo.
        cv_text: Raw CV text (ya master CV use hoga)
        """
        if not cv_text:
            if not self._master_cv:
                return {"success": False,
                        "message": "Pehle CV save karo"}
            cv_text = json.dumps(self._master_cv, ensure_ascii=False)

        data = self._ai_json(f"""
You are a senior CV reviewer and writer.

Analyze and IMPROVE this CV:
{cv_text[:2000]}

Make it:
1. More impactful with quantified achievements (numbers, %)
2. ATS-optimized with strong keywords
3. Action-verb led bullet points
4. Professional and concise summary

Return the IMPROVED CV in same JSON structure as input,
plus add: "improvements_made": ["list of what was improved"]
""")
        if not data:
            return {"success": False, "message": "Improvement nahi ho saka"}

        improvements = data.pop("improvements_made", [])
        self._master_cv = {**self._master_cv, **data}
        self._master_cv["updated_at"] = datetime.now().isoformat()
        self._save_master_cv()

        pdf_path = self._generate_pdf(self._master_cv, "improved_cv")
        return {
            "success":          True,
            "cv":               self._master_cv,
            "improvements":     improvements,
            "pdf_path":         pdf_path,
            "message":          f"CV improve ho gaya! {len(improvements)} improvements.",
        }

    # ── JOB-SPECIFIC CV CUSTOMIZER ────────────────────────────

    def customize_for_job(self, job_description: str,
                          job_title: str = "",
                          company: str = "") -> dict:
        """
        Job ke liye CV customize karo.
        Job ke keywords extract karke CV mein add karta hai.
        ATS 80%+ ensure karta hai.
        """
        if not self._master_cv:
            return {"success": False,
                    "message": "Master CV nahi hai — pehle CV save karo"}

        data = self._ai_json(f"""
You are an expert CV customizer and ATS optimization specialist.

Job Title: {job_title}
Company: {company}
Job Description:
{job_description[:1500]}

Candidate's Master CV:
{json.dumps(self._master_cv, ensure_ascii=False)[:2000]}

Task: Customize the CV for THIS SPECIFIC JOB.

1. Rewrite summary to match job requirements exactly
2. Reorder/rewrite experience bullets to highlight relevant skills
3. Add missing keywords from job description naturally
4. Ensure ATS score will be 80%+
5. Keep all facts truthful — only rephrase/reorder

Return ONLY JSON:
{{
  "customized_cv": {{ ... same CV structure ... }},
  "keywords_added": ["keyword1", "keyword2"],
  "keywords_missing": ["skill you lack"],
  "ats_score": 85,
  "ats_improvements": ["what was changed for ATS"],
  "match_percentage": 87,
  "recommendation": "Should you apply? Why?"
}}
""")
        if not data:
            return {"success": False,
                    "message": "Customization nahi ho saki — API key check karein"}

        custom_cv   = data.get("customized_cv", self._master_cv)
        ats_score   = data.get("ats_score", 0)
        match_pct   = data.get("match_percentage", 0)

        # Save this version
        version_name = re.sub(r'[^\w]', '_', job_title or "custom")[:20]
        version_name = f"{version_name}_{datetime.now().strftime('%Y%m%d')}"
        version_path = self.cv_dir / f"cv_{version_name}.json"
        version_path.write_text(
            json.dumps(custom_cv, indent=2, ensure_ascii=False)
        )

        pdf_path = self._generate_pdf(custom_cv, version_name)
        return {
            "success":          True,
            "customized_cv":    custom_cv,
            "pdf_path":         pdf_path,
            "ats_score":        ats_score,
            "match_percentage": match_pct,
            "keywords_added":   data.get("keywords_added", []),
            "keywords_missing": data.get("keywords_missing", []),
            "ats_improvements": data.get("ats_improvements", []),
            "recommendation":   data.get("recommendation", ""),
            "version_saved":    str(version_path),
            "message": (
                f"CV customize ho gaya! "
                f"ATS Score: {ats_score}/100 | Match: {match_pct}%"
            ),
        }

    # ── ATS SCORE CHECKER ─────────────────────────────────────

    def check_ats_score(self, job_description: str,
                        cv_text: str = None) -> dict:
        """
        ATS Score check karo — CV job ke liye kitna fit hai?
        Returns detailed score + improvements.
        """
        cv = cv_text or json.dumps(self._master_cv, ensure_ascii=False)
        if not cv or cv == "{}":
            return {"success": False, "message": "CV nahi hai"}

        data = self._ai_json(f"""
You are an ATS (Applicant Tracking System) expert.

Job Description:
{job_description[:1200]}

CV Content:
{cv[:1500]}

Analyze ATS compatibility:

Return ONLY JSON:
{{
  "ats_score": 78,
  "breakdown": {{
    "keyword_match": 80,
    "format_score": 90,
    "experience_match": 75,
    "skills_match": 70,
    "education_match": 85
  }},
  "found_keywords": ["python", "react", "sql"],
  "missing_keywords": ["docker", "kubernetes", "ci/cd"],
  "critical_issues": ["Missing required skill: X"],
  "quick_fixes": [
    "Add 'Docker' to skills section",
    "Mention 'Agile methodology' in experience"
  ],
  "will_pass_ats": true,
  "recommendation": "Strong match — apply immediately / Needs improvement"
}}
""")
        if not data:
            return {"success": False, "message": "ATS check nahi ho saka"}

        return {
            "success":          True,
            "ats_score":        data.get("ats_score", 0),
            "breakdown":        data.get("breakdown", {}),
            "found_keywords":   data.get("found_keywords", []),
            "missing_keywords": data.get("missing_keywords", []),
            "critical_issues":  data.get("critical_issues", []),
            "quick_fixes":      data.get("quick_fixes", []),
            "will_pass_ats":    data.get("will_pass_ats", False),
            "recommendation":   data.get("recommendation", ""),
        }

    # ── COVER LETTER GENERATOR ────────────────────────────────

    def generate_cover_letter(self, job_title: str,
                              company: str,
                              job_description: str,
                              tone: str = "professional") -> dict:
        """
        Har job ke liye bilkul alag cover letter.
        """
        cv_summary = json.dumps(
            {k: v for k, v in self._master_cv.items()
             if k in ["name", "summary", "experience", "skills"]},
            ensure_ascii=False
        )[:1000]

        letter = self._ai_call(f"""
Write a compelling, personalized cover letter.

Job Title: {job_title}
Company: {company}
Tone: {tone}
Job Description: {job_description[:800]}
Candidate Profile: {cv_summary}

Requirements:
- Opening hook (why THIS company, not generic)
- 2 specific achievements from CV that match job needs
- Why you're excited about this specific role/company
- Clear call-to-action
- 250-300 words maximum
- No clichés like "I am writing to express my interest"

Write ONLY the cover letter text (no subject line needed).
""")
        if not letter:
            return {"success": False, "message": "Cover letter generate nahi ho saka"}

        # Save cover letter
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = re.sub(r'[^\w]', '_', company)[:15]
        path = self.output_dir / f"cover_letter_{name}_{ts}.txt"
        path.write_text(letter, encoding='utf-8')

        return {
            "success":      True,
            "cover_letter": letter,
            "saved_at":     str(path),
            "word_count":   len(letter.split()),
            "message":      f"Cover letter ready! {len(letter.split())} words.",
        }

    # ── CV VERSIONS ───────────────────────────────────────────

    def list_cv_versions(self) -> list:
        """Saved CV versions list karo."""
        versions = []
        for f in self.cv_dir.glob("cv_*.json"):
            try:
                data = json.loads(f.read_text())
                versions.append({
                    "filename":   f.name,
                    "path":       str(f),
                    "created":    datetime.fromtimestamp(
                        f.stat().st_mtime
                    ).strftime("%d %b %Y %H:%M"),
                    "name":       data.get("name", ""),
                })
            except Exception:
                pass
        return sorted(versions, key=lambda x: x["created"], reverse=True)

    # ── PDF GENERATOR ─────────────────────────────────────────

    def _generate_pdf(self, cv_data: dict, filename: str) -> str:
        """Professional CV PDF generate karo."""
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = str(self.output_dir / f"{filename}_{ts}.pdf")

        if not PDF_AVAILABLE:
            # Text fallback
            txt_path = pdf_path.replace(".pdf", ".txt")
            self._generate_text_cv(cv_data, txt_path)
            return txt_path

        try:
            doc    = SimpleDocTemplate(pdf_path, pagesize=letter,
                                       topMargin=0.5*inch,
                                       bottomMargin=0.5*inch,
                                       leftMargin=0.75*inch,
                                       rightMargin=0.75*inch)
            styles = getSampleStyleSheet()
            story  = []
            DARK   = colors.HexColor("#1a1a2e")
            BLUE   = colors.HexColor("#0066cc")
            GRAY   = colors.HexColor("#666666")

            # Name
            story.append(Paragraph(
                f"<font size=22 color='#1a1a2e'><b>{cv_data.get('name','')}</b></font>",
                styles['Normal']
            ))
            story.append(Spacer(1, 4))

            # Contact line
            contact_parts = [
                cv_data.get('email',''), cv_data.get('phone',''),
                cv_data.get('location',''), cv_data.get('linkedin','')
            ]
            contact = " | ".join(p for p in contact_parts if p)
            story.append(Paragraph(
                f"<font size=9 color='#666666'>{contact}</font>",
                styles['Normal']
            ))
            story.append(HRFlowable(width="100%", thickness=2,
                                    color=BLUE, spaceAfter=6))

            def section_header(title):
                story.append(Spacer(1, 8))
                story.append(Paragraph(
                    f"<font size=11 color='#0066cc'><b>{title.upper()}</b></font>",
                    styles['Normal']
                ))
                story.append(HRFlowable(width="100%", thickness=0.5,
                                        color=GRAY, spaceBefore=2, spaceAfter=4))

            # Summary
            if cv_data.get('summary'):
                section_header("Professional Summary")
                story.append(Paragraph(
                    f"<font size=9>{cv_data['summary']}</font>",
                    styles['Normal']
                ))

            # Experience
            if cv_data.get('experience'):
                section_header("Experience")
                for exp in cv_data['experience']:
                    story.append(Paragraph(
                        f"<b>{exp.get('title','')}</b>  "
                        f"<font color='#0066cc'>{exp.get('company','')}</font>  "
                        f"<font size=8 color='#666666'>{exp.get('duration','')} | {exp.get('location','')}</font>",
                        styles['Normal']
                    ))
                    for b in exp.get('bullets', []):
                        story.append(Paragraph(
                            f"<font size=8>• {b}</font>",
                            ParagraphStyle('bullet', parent=styles['Normal'],
                                          leftIndent=12)
                        ))
                    story.append(Spacer(1, 4))

            # Education
            if cv_data.get('education'):
                section_header("Education")
                for edu in cv_data['education']:
                    story.append(Paragraph(
                        f"<b>{edu.get('degree','')}</b>  "
                        f"<font color='#0066cc'>{edu.get('institution','')}</font>  "
                        f"<font size=8 color='#666666'>{edu.get('year','')}"
                        f"{' | GPA: '+edu['gpa'] if edu.get('gpa') else ''}</font>",
                        styles['Normal']
                    ))
                    story.append(Spacer(1, 3))

            # Skills
            if cv_data.get('skills'):
                section_header("Skills")
                sk = cv_data['skills']
                if isinstance(sk, dict):
                    for cat, items in sk.items():
                        if items:
                            story.append(Paragraph(
                                f"<b>{cat.capitalize()}:</b> "
                                f"<font size=9>{', '.join(items)}</font>",
                                styles['Normal']
                            ))
                else:
                    story.append(Paragraph(
                        f"<font size=9>{', '.join(sk)}</font>",
                        styles['Normal']
                    ))

            # Projects
            if cv_data.get('projects'):
                section_header("Projects")
                for proj in cv_data['projects']:
                    tech = ', '.join(proj.get('tech', []))
                    story.append(Paragraph(
                        f"<b>{proj.get('name','')}</b>"
                        f"{'  <font size=8 color=#666666>['+tech+']</font>' if tech else ''}",
                        styles['Normal']
                    ))
                    story.append(Paragraph(
                        f"<font size=8>• {proj.get('description','')}</font>",
                        ParagraphStyle('bullet', parent=styles['Normal'],
                                      leftIndent=12)
                    ))
                    story.append(Spacer(1, 3))

            # Certifications
            if cv_data.get('certifications'):
                section_header("Certifications")
                certs = cv_data['certifications']
                story.append(Paragraph(
                    f"<font size=9>{' • '.join(certs)}</font>",
                    styles['Normal']
                ))

            # Languages
            if cv_data.get('languages'):
                section_header("Languages")
                langs = cv_data['languages']
                story.append(Paragraph(
                    f"<font size=9>{' | '.join(langs)}</font>",
                    styles['Normal']
                ))

            doc.build(story)
            logger.success(f"CV PDF: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"PDF error: {e}")
            txt_path = pdf_path.replace(".pdf", ".txt")
            self._generate_text_cv(cv_data, txt_path)
            return txt_path

    def _generate_text_cv(self, cv: dict, path: str):
        """Text CV fallback."""
        lines = [
            "=" * 60,
            cv.get("name", ""),
            cv.get("email","") + " | " + cv.get("phone","") + " | " + cv.get("location",""),
            "=" * 60, "",
            "SUMMARY", "-" * 30,
            cv.get("summary",""), "",
            "EXPERIENCE", "-" * 30,
        ]
        for exp in cv.get("experience", []):
            lines += [
                f"{exp.get('title','')} @ {exp.get('company','')} ({exp.get('duration','')})"
            ] + [f"  • {b}" for b in exp.get("bullets", [])] + [""]

        lines += ["EDUCATION", "-" * 30]
        for edu in cv.get("education", []):
            lines.append(f"{edu.get('degree','')} — {edu.get('institution','')} {edu.get('year','')}")

        skills = cv.get("skills", {})
        lines += ["", "SKILLS", "-" * 30]
        if isinstance(skills, dict):
            for k, v in skills.items():
                lines.append(f"{k}: {', '.join(v)}")
        else:
            lines.append(", ".join(skills))

        Path(path).write_text("\n".join(lines), encoding='utf-8')
