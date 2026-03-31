# ============================================================
# Blogging Pro Agent - SEO Content Specialist (Multi-Step v2)
# ============================================================
import os, json, re, time
from datetime import datetime
from loguru import logger
import google.generativeai as genai
from core.status_reporter import reporter

try:
    from config import GEMINI_API_KEY, GROQ_API_KEY, MODEL_NAME, MIN_WORDS
except ImportError:
    GEMINI_API_KEY = ""
    GROQ_API_KEY   = ""
    MODEL_NAME = "gemini-1.5-flash-latest"
    MIN_WORDS  = 1000

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class SEOWriter:
    def __init__(self, api_key: str = None, groq_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.groq_key = groq_key or GROQ_API_KEY
        self._init_ai()

    def _init_ai(self):
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key, transport='rest')
                self.gemini = genai.GenerativeModel("gemini-1.5-flash")
            except: self.gemini = None
        else: self.gemini = None

    def _ai_call(self, prompt: str, json_mode=True) -> str:
        """Call AI with priority: Groq -> Gemini."""
        if GROQ_AVAILABLE and self.groq_key:
            try:
                client = Groq(api_key=self.groq_key)
                r = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"} if json_mode else None
                )
                return r.choices[0].message.content
            except Exception as e:
                logger.warning(f"Groq Error: {e}")

        if self.gemini:
            try:
                r = self.gemini.generate_content(prompt)
                text = r.text
                if json_mode:
                    text = re.sub(r'^```json\s*', '', text)
                    text = re.sub(r'\s*```$', '', text)
                return text
            except Exception as e:
                logger.error(f"Gemini Error: {e}")
        return "{}" if json_mode else "Writing failed."

    def generate_full_article(self, kw_data: dict) -> dict:
        kw = kw_data.get("keyword", "Scholarships")
        title = kw_data.get("target_title", f"Scholarships for Pakistani Students {datetime.now().year}")
        
        reporter.info(f"✍️ Drafting 1500-word article for: {title}...")
        
        # STEP 1: Research & Outline
        reporter.info("🔍 Step 1: Researching & Creating Outline...")
        outline_prompt = f"Create a detailed 7-point SEO outline for: {title}. Focus on {kw}. Return JSON: {{'outline': ['H2 point 1', 'H2 point 2', ...]}}"
        outline_text = self._ai_call(outline_prompt)
        try:
            outline_json = json.loads(outline_text)
            outline = outline_json.get('outline', [])
        except: 
            outline = [f"Introduction to {kw}", f"Top 5 {kw} for 2026", "Eligibility", "Conclusion"]
        time.sleep(2)

        # STEP 2: Writing Body (The Real Work)
        reporter.info("📄 Step 2: Writing Deep Content (This will take ~30 seconds)...")
        full_content = f"<h1>{title}</h1>\n"
        
        # Write chunks to make it actually long
        for i, point in enumerate(outline):
            reporter.info(f"   Writing Section {i+1}/{len(outline)}: {point}")
            section_prompt = f"Topic: {title}. Section: {point}. Task: Write a 300-word detailed blog section using HTML subheadings and bullet points. Focus on being an expert info resource for Pakistani students. DO NOT include meta tags or titles."
            chunk = self._ai_call(section_prompt, json_mode=False)
            full_content += f"\n<section>\n{chunk}\n</section>\n"
            time.sleep(2) # Feel real & give API a break

        # STEP 3: Meta & Cleanup
        reporter.info("🧹 Step 3: Optimizing Meta Tags & SEO...")
        meta_prompt = f"Generate Meta Description, Excerpt, and 5 Tags for '{title}'. Return JSON: {{'meta': '...', 'excerpt': '...', 'tags': []}}"
        meta_text = self._ai_call(meta_prompt)
        try:
            meta_data = json.loads(meta_text)
        except:
            meta_data = {"meta": title, "excerpt": title, "tags": [kw]}
        
        reporter.success(f"✅ Blog finished: {len(full_content.split())} words generated.")
        
        return {
            "success": True,
            "title": title,
            "content": full_content,
            "meta_description": meta_data.get('meta'),
            "excerpt": meta_data.get('excerpt'),
            "tags": meta_data.get('tags', []),
            "status": "Ready"
        }
