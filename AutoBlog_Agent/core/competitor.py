# ============================================================
# Blogging Pro Agent - Competitor Research Engine
# ============================================================
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from loguru import logger
from urllib.parse import urlparse, urljoin
from core.status_reporter import reporter

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/120.0.0.0 Safari/537.36"
}


class CompetitorResearcher:
    """Analyzes competitor websites to find winning keywords."""

    def __init__(self):
        self.groq = Groq(api_key=GROQ_API_KEY) if GROQ_AVAILABLE and GROQ_API_KEY else None

    # ── STEP 1: Scrape your own website ────────────────────────────────────
    def analyze_my_site(self, url: str) -> dict:
        """Scan the user's website to understand their niche and content."""
        logger.info(f"🔍 Analyzing your website: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")

            # Extract key info
            title   = soup.find("title").get_text(strip=True) if soup.find("title") else "N/A"
            desc_tag = soup.find("meta", attrs={"name": "description"})
            desc    = desc_tag["content"] if desc_tag else "N/A"
            body    = " ".join(soup.get_text(" ", strip=True).split())[:3000]

            posts = []
            for a in soup.find_all("a", href=True)[:30]:
                href = a["href"]
                txt  = a.get_text(strip=True)
                if len(txt) > 10 and ("/" in href):
                    posts.append(txt)

            logger.success(f"Site scraped: {title}")
            return {"url": url, "title": title, "description": desc,
                    "sample_text": body, "recent_posts": posts[:15]}
        except Exception as e:
            logger.error(f"Site scrape failed: {e}")
            return {"url": url, "title": "Unknown", "error": str(e)}

    # ── STEP 2: Find Competitors ────────────────────────────────────────────
    def find_competitors(self, niche: str, site_url: str) -> list:
        """Use AI to suggest top competitor websites for the niche."""
        logger.info(f"🔎 Finding competitors for niche: {niche}")
        if not self.groq: return []

        prompt = f"""
        You are an SEO expert. For the niche "{niche}", list 5 competitor blog websites
        that rank well in Google. Site to exclude: {site_url}
        
        Return valid JSON:
        {{"competitors": [
            {{"name": "Site Name", "url": "https://...", "reason": "Why it ranks well"}}
        ]}}
        """
        try:
            resp = self.groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            return data.get("competitors", [])
        except Exception as e:
            logger.error(f"Competitor find failed: {e}")
            return []

    # ── STEP 3: Scrape competitor content ──────────────────────────────────
    def scrape_competitor(self, url: str) -> dict:
        """Scrape a competitor's recent posts and keywords."""
        logger.info(f"📰 Scraping competitor: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "lxml")

            titles = []
            for tag in soup.find_all(["h1", "h2", "h3", "h4"])[:20]:
                t = tag.get_text(strip=True)
                if len(t) > 8: titles.append(t)

            for a in soup.find_all("a", href=True)[:50]:
                txt = a.get_text(strip=True)
                if len(txt) > 10 and len(txt) < 100:
                    titles.append(txt)

            body = " ".join(soup.get_text(" ", strip=True).split())[:2000]
            return {"url": url, "headings": titles[:20], "sample": body}
        except Exception as e:
            logger.error(f"Scrape failed for {url}: {e}")
            return {"url": url, "headings": [], "error": str(e)}

    # ── STEP 4: AI Keyword Extraction from competitors ─────────────────────
    def extract_winning_keywords(self, competitor_data: list, my_niche: str) -> list:
        """Use AI to extract the best keywords from competitor data."""
        logger.info("🧠 Extracting winning keywords from competitor data...")
        if not self.groq: return []

        combined = "\n".join([
            f"Site: {c.get('url')}\nHeadings: {', '.join(c.get('headings', [])[:10])}"
            for c in competitor_data
        ])

        prompt = f"""
        You are an expert SEO analyst. I run a blog about "{my_niche}".
        
        These are my competitors' top posts/headings:
        ---
        {combined[:3000]}
        ---
        
        Based on this competitor analysis:
        1. Identify the TOP 5 keywords they rank for that I should target TODAY.
        2. Suggest a unique blog title for each keyword that is better than competitors.
        3. Focus on low-competition but high-traffic potential keywords.
        
        Return valid JSON:
        {{"winning_keywords": [
            {{
                "keyword": "...",
                "competitor_site": "...",
                "suggested_title": "...",
                "search_intent": "informational/commercial",
                "priority": "High/Medium",
                "reason": "Why target this keyword today"
            }}
        ]}}
        """
        try:
            resp = self.groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(resp.choices[0].message.content)
            return data.get("winning_keywords", [])
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []

    # ── FULL PIPELINE ───────────────────────────────────────────────────────
    def full_research(self, my_url: str, my_niche: str) -> list:
        """Run the complete competitor research pipeline."""
        # 1. Analyze user's own site
        reporter.info(f"🔍 Analyzing your website: {my_url}")
        my_site = self.analyze_my_site(my_url)
        
        # 2. Find competitors
        reporter.info(f"🔎 Finding competitors for niche: {my_niche}")
        competitors = self.find_competitors(my_niche, my_url)
        reporter.success(f"Found {len(competitors)} potential competitors.")
        
        # 3. Scrape each competitor
        scraped = []
        for i, comp in enumerate(competitors[:3]): # Limit to 3 to be fast
            url = comp.get("url", "")
            reporter.info(f"📰 Scraping competitor {i+1}/3: {url}")
            data = self.scrape_competitor(url)
            if data:
                scraped.append(data)
        
        # 4. Extract winning keywords
        reporter.info("🧠 Brainstorming winning keywords with AI...")
        keywords = self.extract_winning_keywords(scraped, my_niche)
        reporter.success(f"✅ Research complete! Found {len(keywords)} hot keywords.")
        return keywords
