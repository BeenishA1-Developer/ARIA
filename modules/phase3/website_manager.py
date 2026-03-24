# ============================================================
# ARIA Phase 3 — Website Manager + SEO Auto-Poster
# Blog posts, Service pages, SEO optimization, Git push
# ============================================================

import os
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class WebsiteManager:
    """
    ARIA Phase 3 — Website Content Manager.

    ✅ SEO-optimized blog posts generate + website pe add
    ✅ H1/H2/H3 auto-structured
    ✅ Meta title + description + keywords auto
    ✅ Schema markup for Google SEO
    ✅ Reading time calculate
    ✅ Internal linking suggestions
    ✅ React component banata hai + file mein save
    ✅ Git commit + push automatic
    ✅ Service pages generate
    ✅ Existing pages SEO score (0-100)
    ✅ Image alt tags auto-generate
    ✅ Sitemap update
    """

    def __init__(self, gemini_api_key: str = None,
                 website_path: str = None):
        self.api_key      = gemini_api_key or os.getenv("GEMINI_API_KEY","")
        self.website_path = Path(website_path) if website_path else None
        self.output_dir   = Path("outputs/website")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._ai          = None
        self._init_ai()
        logger.info("Website Manager initialized")

    def _init_ai(self):
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self._ai = genai.GenerativeModel("gemini-1.5-flash")
                logger.success("Website Manager AI ready")
            except Exception as e:
                logger.error(f"AI: {e}")

    def _ai_call(self, prompt: str) -> str:
        if not self._ai:
            return ""
        try:
            return self._ai.generate_content(prompt).text.strip()
        except Exception as e:
            logger.error(f"AI: {e}")
            return ""

    def _ai_json(self, prompt: str) -> dict:
        text = self._ai_call(prompt)
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$',    '', text)
        try:
            return json.loads(text)
        except Exception:
            return {}

    # ── SEO BLOG POST GENERATOR ───────────────────────────────

    def generate_blog_post(self, topic: str,
                            keywords: list = None,
                            word_count: int = 1000) -> dict:
        """
        SEO-optimized blog post generate karo.
        """
        kw_str = ", ".join(keywords) if keywords else topic

        data = self._ai_json(f"""
Write a complete SEO-optimized blog post.

Topic: "{topic}"
Target Keywords: {kw_str}
Word Count: ~{word_count} words

Return ONLY JSON:
{{
  "meta": {{
    "title": "SEO title (50-60 chars)",
    "description": "Meta description (150-160 chars)",
    "keywords": ["kw1", "kw2", "kw3"],
    "slug": "url-friendly-slug",
    "reading_time": "5 min read",
    "word_count": 1000
  }},
  "schema_markup": {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Article title",
    "datePublished": "{datetime.now().strftime('%Y-%m-%d')}",
    "author": {{"@type": "Person", "name": "Author Name"}}
  }},
  "content": {{
    "h1": "Main heading",
    "intro": "Compelling introduction paragraph",
    "sections": [
      {{
        "h2": "Section heading",
        "content": "Section content",
        "h3_subsections": [
          {{"h3": "Subsection", "content": "Details"}}
        ]
      }}
    ],
    "conclusion": "Strong conclusion with CTA",
    "internal_links": [
      {{"anchor_text": "related topic", "suggested_url": "/blog/related-topic"}}
    ]
  }},
  "image_suggestions": [
    {{"alt_text": "Descriptive alt text", "caption": "Image caption"}}
  ],
  "seo_score": 88,
  "seo_tips": ["Add more internal links", "Include video"]
}}
""")
        if not data:
            return {"success": False, "message": "Blog post generate nahi ho saka"}

        # Generate React component
        react_component = self._generate_react_blog(data, topic)

        # Save files
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = data.get("meta", {}).get("slug",
               topic.lower().replace(" ", "-"))

        json_path  = self.output_dir / f"blog_{slug}_{ts}.json"
        react_path = self.output_dir / f"Blog_{slug.replace('-','_').title()}_{ts}.jsx"

        json_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )
        if react_component:
            react_path.write_text(react_component, encoding='utf-8')

        return {
            "success":        True,
            "topic":          topic,
            "meta":           data.get("meta", {}),
            "content":        data.get("content", {}),
            "schema":         data.get("schema_markup", {}),
            "seo_score":      data.get("seo_score", 0),
            "react_path":     str(react_path) if react_component else None,
            "json_path":      str(json_path),
            "message": (
                f"Blog post ready! SEO Score: {data.get('seo_score',0)}/100 | "
                f"Reading time: {data.get('meta',{}).get('reading_time','')}"
            ),
        }

    def _generate_react_blog(self, data: dict, topic: str) -> str:
        """React blog component generate karo."""
        meta    = data.get("meta", {})
        content = data.get("content", {})
        slug    = meta.get("slug", topic.lower().replace(" ","-"))
        comp    = slug.replace("-","_").title().replace("_","")

        sections_jsx = ""
        for sec in content.get("sections", []):
            sections_jsx += f"""
      <section className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          {sec.get('h2','')}
        </h2>
        <p className="text-gray-600 leading-relaxed">
          {sec.get('content','')}
        </p>
      </section>"""

        return f'''import React from 'react';
import {{ Helmet }} from 'react-helmet';

const {comp}Blog = () => {{
  return (
    <>
      <Helmet>
        <title>{meta.get('title','')}</title>
        <meta name="description" content="{meta.get('description','')}" />
        <meta name="keywords" content="{', '.join(meta.get('keywords',[]))}" />
        <script type="application/ld+json">
          {{JSON.stringify({json.dumps(data.get("schema_markup",{}))})}}
        </script>
      </Helmet>

      <article className="max-w-4xl mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {content.get('h1','')}
          </h1>
          <p className="text-sm text-gray-500">
            {meta.get('reading_time','')} • {datetime.now().strftime('%B %d, %Y')}
          </p>
        </header>

        <div className="prose prose-lg">
          <p className="text-lg text-gray-700 mb-8 leading-relaxed">
            {content.get('intro','')}
          </p>
{sections_jsx}
          <div className="bg-blue-50 p-6 rounded-lg mt-8">
            <p className="text-gray-700 font-medium">
              {content.get('conclusion','')}
            </p>
          </div>
        </div>
      </article>
    </>
  );
}};

export default {comp}Blog;
'''

    # ── SERVICE PAGE GENERATOR ────────────────────────────────

    def generate_service_page(self, service: str,
                               features: list = None) -> dict:
        """Complete service page generate karo."""
        data = self._ai_json(f"""
Create a complete, conversion-optimized service page.

Service: "{service}"
Features: {features or ['Professional', 'Fast', 'Affordable']}

Return ONLY JSON:
{{
  "meta": {{
    "title": "{service} Services | Professional & Affordable",
    "description": "Meta description",
    "keywords": ["keyword1", "keyword2"]
  }},
  "hero": {{
    "headline": "Main hero headline",
    "subheadline": "Supporting text",
    "cta_text": "Get Started Today",
    "cta_url": "/contact"
  }},
  "features": [
    {{"icon": "🚀", "title": "Feature", "description": "Details"}}
  ],
  "process": [
    {{"step": 1, "title": "Discovery", "description": "We understand your needs"}}
  ],
  "faq": [
    {{"q": "Common question?", "a": "Helpful answer"}}
  ],
  "pricing_hint": "Starting from $X",
  "seo_score": 90
}}
""")
        if not data:
            return {"success": False, "message": "Service page nahi bani"}

        # Generate React component
        react_code = self._generate_service_react(data, service)

        ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
        svc_slug  = service.lower().replace(" ", "-")
        comp_name = service.replace(" ", "").title()
        path      = self.output_dir / f"{comp_name}Page_{ts}.jsx"

        if react_code:
            path.write_text(react_code, encoding='utf-8')

        return {
            "success":    True,
            "service":    service,
            "data":       data,
            "react_path": str(path),
            "seo_score":  data.get("seo_score", 0),
            "message":    f"Service page ready! File: {path.name}",
        }

    def _generate_service_react(self, data: dict, service: str) -> str:
        """Service page React component."""
        comp = service.replace(" ","").title()
        hero = data.get("hero", {})
        feats = data.get("features", [])
        feats_jsx = "\n".join([
            f'''        <div className="p-6 bg-white rounded-xl shadow-md">
          <span className="text-3xl">{f.get('icon','⭐')}</span>
          <h3 className="text-lg font-semibold mt-2">{f.get('title','')}</h3>
          <p className="text-gray-600 mt-1">{f.get('description','')}</p>
        </div>'''
            for f in feats[:6]
        ])

        return f'''import React from 'react';

const {comp}Page = () => (
  <div className="min-h-screen bg-gray-50">
    {{/* Hero */}}
    <section className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-20 px-4 text-center">
      <h1 className="text-5xl font-bold mb-4">{hero.get('headline','')}</h1>
      <p className="text-xl mb-8 opacity-90">{hero.get('subheadline','')}</p>
      <a href="{hero.get('cta_url','/contact')}"
         className="bg-white text-blue-600 px-8 py-4 rounded-full font-bold text-lg hover:shadow-xl transition-all">
        {hero.get('cta_text','Get Started')}
      </a>
    </section>

    {{/* Features */}}
    <section className="max-w-6xl mx-auto py-16 px-4">
      <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
        Why Choose Us?
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
{feats_jsx}
      </div>
    </section>

    {{/* CTA */}}
    <section className="bg-blue-600 text-white py-16 text-center">
      <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
      <a href="/contact"
         className="bg-white text-blue-600 px-8 py-4 rounded-full font-bold text-lg">
        Contact Us Today
      </a>
    </section>
  </div>
);

export default {comp}Page;
'''

    # ── SEO SCORE CHECKER ─────────────────────────────────────

    def check_seo_score(self, page_content: str,
                        target_keyword: str = "") -> dict:
        """Existing page ka SEO score check karo (0-100)."""
        data = self._ai_json(f"""
Analyze SEO score for this webpage content:

Target Keyword: "{target_keyword}"
Content (first 1500 chars):
{page_content[:1500]}

Return ONLY JSON:
{{
  "overall_score": 72,
  "breakdown": {{
    "title_optimization":       85,
    "meta_description":         70,
    "keyword_density":          65,
    "heading_structure":        80,
    "content_length":           75,
    "internal_links":           50,
    "image_alt_tags":           60,
    "page_speed_estimate":      80,
    "mobile_friendly_estimate": 90
  }},
  "critical_issues": ["Missing H1 tag", "No meta description"],
  "quick_wins": [
    "Add target keyword in H1",
    "Write meta description (150-160 chars)",
    "Add 2-3 internal links"
  ],
  "keyword_usage": {{
    "in_title":       true,
    "in_h1":          false,
    "in_first_100":   true,
    "density":        "1.2%"
  }},
  "competitor_gap": "Competitors average 85/100 — you need 13 more points"
}}
""")
        if not data:
            return {"success": False, "message": "SEO check nahi ho saka"}
        return {"success": True, "keyword": target_keyword, **data}

    # ── GIT OPERATIONS ────────────────────────────────────────

    def git_commit_push(self, files: list = None,
                         message: str = None,
                         website_path: str = None) -> dict:
        """Git commit + push karo."""
        repo_path = website_path or str(self.website_path or ".")

        if not Path(repo_path).joinpath(".git").exists():
            return {
                "success": False,
                "message": f"Git repo nahi mila: {repo_path}",
            }
        commit_msg = message or (
            f"ARIA: Add content — {datetime.now().strftime('%d %b %Y %H:%M')}"
        )
        try:
            cmds = [
                ["git", "-C", repo_path, "add", "."],
                ["git", "-C", repo_path, "commit", "-m", commit_msg],
                ["git", "-C", repo_path, "push"],
            ]
            outputs = []
            for cmd in cmds:
                r = subprocess.run(cmd, capture_output=True, text=True)
                outputs.append({
                    "cmd":    " ".join(cmd[2:]),
                    "output": r.stdout.strip() or r.stderr.strip(),
                    "ok":     r.returncode == 0,
                })
            success = all(o["ok"] for o in outputs)
            logger.info(f"Git push: {'success' if success else 'failed'}")
            return {
                "success":    success,
                "commit_msg": commit_msg,
                "outputs":    outputs,
                "message":    ("Code push ho gaya! ✅"
                               if success else "Git push fail — check credentials"),
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── IMAGE ALT TAGS ────────────────────────────────────────

    def generate_alt_tags(self, image_descriptions: list) -> list:
        """Images ke liye SEO alt tags generate karo."""
        results = []
        for desc in image_descriptions:
            alt = self._ai_call(
                f"Write a concise SEO alt text (under 125 chars) for: {desc}. "
                f"Be descriptive and include relevant keywords naturally."
            )
            results.append({
                "image":   desc,
                "alt_tag": alt or desc[:125],
            })
        return results

    # ── WEBSITE GENERATOR (Full Stack) ───────────────────────

    def generate_full_website(self, requirements: str) -> dict:
        """
        Client requirements se complete website code generate karo.
        React + TypeScript + Node.js + MongoDB
        """
        data = self._ai_json(f"""
Generate a complete full-stack web application based on:
{requirements[:800]}

Return ONLY JSON:
{{
  "project_name": "project-name",
  "tech_stack": {{
    "frontend": "React + TypeScript + Tailwind CSS",
    "backend":  "Node.js + Express",
    "database": "MongoDB + Mongoose",
    "auth":     "JWT",
    "hosting":  "Vercel (frontend) + Railway (backend)"
  }},
  "folder_structure": [
    "frontend/src/components/",
    "frontend/src/pages/",
    "backend/routes/",
    "backend/models/"
  ],
  "key_features": ["Feature 1", "Feature 2"],
  "api_endpoints": [
    {{"method": "GET",  "endpoint": "/api/users", "description": "Get all users"}},
    {{"method": "POST", "endpoint": "/api/auth/login", "description": "Login"}}
  ],
  "setup_commands": [
    "npm create vite@latest frontend",
    "cd frontend && npm install",
    "npm install express mongoose dotenv cors"
  ],
  "deployment_guide": {{
    "frontend": "Push to GitHub → Import in Vercel → Deploy",
    "backend":  "Push to GitHub → Create Railway project → Add env vars"
  }},
  "estimated_time": "2-3 hours"
}}
""")
        if not data:
            return {"success": False, "message": "Website plan generate nahi ho saka"}

        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"website_plan_{ts}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

        return {
            "success":    True,
            "plan":       data,
            "saved_at":   str(path),
            "message":    f"Website plan ready! Tech: {data.get('tech_stack',{}).get('frontend','')}",
        }
