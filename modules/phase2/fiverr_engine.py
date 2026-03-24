# ============================================================
# ARIA Phase 2 — Fiverr Growth Engine v2 (COMPLETE)
# Keywords, Frequency Analyzer, Ranking Detector, PDF Report
# ============================================================

import os
import json
import re
from collections import Counter
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
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("reportlab not installed — PDF reports as text fallback")


class FiverrEngine:
    """
    ARIA Phase 2 — Fiverr Business Intelligence (COMPLETE).
    ✅ Top 30 keywords
    ✅ Keyword frequency analyzer
    ✅ Competitor analysis
    ✅ Gig title optimizer
    ✅ SEO tags generator (30 tags)
    ✅ Description enhancer
    ✅ PDF performance report
    ✅ Pricing strategy comparison
    ✅ Ranking opportunity detector
    """

    def __init__(self, gemini_api_key: str = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._ai = None
        self._init_ai()
        self.output_dir = Path("outputs/fiverr")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Fiverr Engine v2 initialized")

    def _init_ai(self):
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self._ai = genai.GenerativeModel("gemini-1.5-flash")
                logger.success("Fiverr AI ready")
            except Exception as e:
                logger.error(f"AI init: {e}")

    def _ai_json(self, prompt: str) -> dict:
        """AI call → JSON parse."""
        if not self._ai:
            return {}
        try:
            resp = self._ai.generate_content(prompt)
            text = resp.text.strip()
            text = re.sub(r'^```json\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI JSON parse error: {e}")
            return {}

    # ── 1. KEYWORD RESEARCH ───────────────────────────────────

    def get_keywords(self, service_category: str, count: int = 30) -> dict:
        """Top keywords — AI powered."""
        data = self._ai_json(f"""
You are a Fiverr SEO expert. Generate top {count} high-performing keywords
for Fiverr gig category: "{service_category}"

Return ONLY JSON:
{{
  "category": "{service_category}",
  "keywords": [
    {{"keyword": "...", "difficulty": "low/medium/high",
      "volume": "low/medium/high", "type": "short/long-tail",
      "monthly_searches": "approx number"}}
  ],
  "top_3": ["kw1", "kw2", "kw3"],
  "tip": "one actionable tip"
}}
""")
        if not data:
            return self._fallback_keywords(service_category)
        logger.success(f"Keywords: {service_category}")
        return {"success": True, **data}

    def _fallback_keywords(self, category: str) -> dict:
        kws = [
            {"keyword": category,              "difficulty": "high",   "volume": "high",   "type": "short",     "monthly_searches": "10000+"},
            {"keyword": f"professional {category}", "difficulty": "medium", "volume": "high",   "type": "short",     "monthly_searches": "5000+"},
            {"keyword": f"{category} service",      "difficulty": "medium", "volume": "medium", "type": "short",     "monthly_searches": "3000+"},
            {"keyword": f"custom {category}",       "difficulty": "low",    "volume": "medium", "type": "short",     "monthly_searches": "2000+"},
            {"keyword": f"affordable {category} service", "difficulty": "low", "volume": "medium", "type": "long-tail", "monthly_searches": "1000+"},
            {"keyword": f"{category} for small business",  "difficulty": "low", "volume": "low",    "type": "long-tail", "monthly_searches": "500+"},
        ]
        return {"success": True, "category": category, "keywords": kws,
                "top_3": [k["keyword"] for k in kws[:3]],
                "tip": f"Use '{category}' in your gig title and opening line."}

    # ── 2. KEYWORD FREQUENCY ANALYZER ────────────────────────

    def analyze_keyword_frequency(self, text_samples: list,
                                   top_n: int = 20) -> dict:
        """
        Keyword frequency analyze karo — competitor titles/descriptions se.
        text_samples: list of gig titles or descriptions
        Returns: Most used keywords with frequency count
        """
        # Stop words
        stop_words = {
            'i', 'will', 'you', 'your', 'the', 'a', 'an', 'and', 'or',
            'for', 'in', 'to', 'of', 'with', 'is', 'are', 'that', 'this',
            'it', 'be', 'do', 'can', 'get', 'my', 'me', 'we', 'our',
            'by', 'on', 'at', 'from', 'up', 'out', 'as', 'into', 'so',
            'have', 'all', 'any', 'just', 'its', 'has', 'was', 'were'
        }

        all_words   = []
        all_phrases = []

        for text in text_samples:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            words = [w for w in words if w not in stop_words]
            all_words.extend(words)

            # Bigrams (2-word phrases)
            for i in range(len(words) - 1):
                all_phrases.append(f"{words[i]} {words[i+1]}")

        word_freq   = Counter(all_words).most_common(top_n)
        phrase_freq = Counter(all_phrases).most_common(top_n // 2)

        result = {
            "success":         True,
            "samples_analyzed": len(text_samples),
            "top_keywords": [
                {"keyword": kw, "frequency": count,
                 "percentage": round(count / max(len(text_samples), 1) * 100, 1)}
                for kw, count in word_freq
            ],
            "top_phrases": [
                {"phrase": ph, "frequency": count}
                for ph, count in phrase_freq
            ],
            "total_unique_keywords": len(set(all_words)),
            "recommendation": (
                f"Most used keyword: '{word_freq[0][0]}' — "
                f"use it in your title and first line"
                if word_freq else "Add more text samples for better analysis"
            )
        }
        logger.success(f"Keyword frequency: {len(text_samples)} samples analyzed")
        return result

    # ── 3. RANKING OPPORTUNITY DETECTOR ──────────────────────

    def detect_ranking_opportunities(self, category: str,
                                      your_stats: dict = None) -> dict:
        """
        Ranking opportunities dhoondo — kahan easy rank mil sakti hai.
        your_stats: {"reviews": 10, "response_time": "1h", "level": "new"}
        """
        data = self._ai_json(f"""
You are a Fiverr ranking expert. Identify ranking opportunities for:
Category: "{category}"
Seller Stats: {json.dumps(your_stats or {{"reviews": 0, "level": "new seller"}})}

Find where a new/growing seller can rank on page 1.

Return ONLY JSON:
{{
  "category": "{category}",
  "opportunities": [
    {{
      "keyword": "specific keyword",
      "difficulty": "low/medium",
      "current_top_sellers": "avg reviews of top 3",
      "your_chance": "high/medium/low",
      "strategy": "how to rank for this keyword",
      "estimated_time": "weeks to rank"
    }}
  ],
  "quick_wins": ["keyword 1", "keyword 2", "keyword 3"],
  "avoid_for_now": ["too competitive keyword 1"],
  "action_plan": [
    "Step 1: ...",
    "Step 2: ...",
    "Step 3: ..."
  ],
  "overall_score": "X/10 — ranking potential"
}}
""")
        if not data:
            return {
                "success": True,
                "category": category,
                "opportunities": [],
                "quick_wins": [
                    f"affordable {category}",
                    f"{category} for startup",
                    f"quick {category} delivery"
                ],
                "action_plan": [
                    "Low competition long-tail keywords target karo",
                    "Gig images professional rakhein",
                    "Response time 1 hour se kam rakhein",
                    "Buyer requests daily check karein"
                ],
                "overall_score": "Depends on niche — AI key set karein"
            }
        logger.success(f"Ranking opportunities: {category}")
        return {"success": True, **data}

    # ── 4. GIG TITLE OPTIMIZER ────────────────────────────────

    def optimize_gig_title(self, current_title: str, category: str) -> dict:
        data = self._ai_json(f"""
Fiverr gig title optimization expert.
Current title: "{current_title}"
Category: "{category}"

Return ONLY JSON:
{{
  "original": "{current_title}",
  "optimized_titles": [
    {{"title": "...", "reason": "...", "score": 85}},
    {{"title": "...", "reason": "...", "score": 82}},
    {{"title": "...", "reason": "...", "score": 79}}
  ],
  "best_pick": "the single best title",
  "improvements": ["what was wrong 1", "what was wrong 2"]
}}
""")
        if not data:
            return {"success": False, "message": "AI key set karein"}
        return {"success": True, **data}

    # ── 5. SEO TAGS GENERATOR ─────────────────────────────────

    def generate_tags(self, gig_title: str, category: str,
                      count: int = 30) -> dict:
        data = self._ai_json(f"""
Generate {count} SEO Fiverr gig tags for:
Title: "{gig_title}" | Category: "{category}"

Rules: 1-2 words, highly relevant, no duplicates, currently searched.

Return ONLY JSON:
{{
  "tags": ["tag1", "tag2", ...],
  "primary_tags": ["top 5 most important"],
  "tip": "how to use these tags"
}}
""")
        if not data:
            # Fallback
            words = [w for w in gig_title.lower().split()
                     if len(w) > 2]
            tags = words + [category.lower(),
                            f"professional {category.lower()}",
                            "freelance", "expert", "fast delivery"]
            return {"success": True, "tags": tags[:count],
                    "primary_tags": tags[:5],
                    "tip": "Put most important tags first"}
        return {"success": True, **data}

    # ── 6. DESCRIPTION ENHANCER ───────────────────────────────

    def enhance_description(self, current_description: str,
                             category: str) -> dict:
        data = self._ai_json(f"""
Fiverr conversion optimization expert.
Enhance this gig description for "{category}":
"{current_description[:400]}"

Return ONLY JSON:
{{
  "enhanced_description": "full improved 150-200 word description",
  "improvements_made": ["improvement 1", "improvement 2", "improvement 3"],
  "keyword_density": "good/needs improvement",
  "conversion_score": 85,
  "cta": "suggested call-to-action line"
}}
""")
        if not data:
            return {"success": False, "message": "AI key set karein"}
        return {"success": True, **data}

    # ── 7. COMPETITOR ANALYSIS ────────────────────────────────

    def analyze_competitors(self, category: str,
                             price_range: str = None) -> dict:
        data = self._ai_json(f"""
Fiverr market research expert.
Analyze competitive landscape for: "{category}"
Price range: {price_range or "all ranges"}

Return ONLY JSON:
{{
  "category": "{category}",
  "market_overview": {{
    "competition_level": "low/medium/high/very high",
    "avg_price_basic": "$X",
    "avg_price_standard": "$X",
    "avg_price_premium": "$X",
    "top_seller_avg_reviews": "X reviews",
    "market_saturation": "0-100"
  }},
  "winning_strategies": ["strategy 1", "strategy 2", "strategy 3"],
  "gap_opportunities": ["opportunity 1", "opportunity 2"],
  "recommended_pricing": {{
    "basic": "$X", "standard": "$X", "premium": "$X"
  }},
  "top_keywords_competitors_use": ["kw1","kw2","kw3","kw4","kw5"],
  "your_advantage": "how to stand out",
  "ranking_tip": "most important tip"
}}
""")
        if not data:
            return {"success": False, "message": "AI key set karein"}
        return {"success": True, **data}

    # ── 8. PRICING STRATEGY ───────────────────────────────────

    def pricing_strategy(self, category: str,
                          experience_level: str = "intermediate") -> dict:
        data = self._ai_json(f"""
Optimal Fiverr pricing for:
Category: "{category}" | Experience: "{experience_level}"

Return ONLY JSON:
{{
  "basic":    {{"price": "$X", "delivery_days": X, "revisions": X, "includes": ["f1","f2"]}},
  "standard": {{"price": "$X", "delivery_days": X, "revisions": X, "includes": ["f1","f2","f3"]}},
  "premium":  {{"price": "$X", "delivery_days": X, "revisions": X, "includes": ["f1","f2","f3","f4"]}},
  "strategy_tip": "key pricing insight",
  "upsell_opportunities": ["upsell 1", "upsell 2"]
}}
""")
        if not data:
            return {"success": False, "message": "AI key set karein"}
        return {"success": True, **data}

    # ── 9. PDF PERFORMANCE REPORT ─────────────────────────────

    def generate_report(self, stats: dict = None) -> dict:
        """
        Weekly Fiverr performance PDF report.
        Real PDF with reportlab — ya text fallback.
        """
        stats = stats or {}
        recs  = self._get_recommendations(stats)
        ts    = datetime.now().strftime("%Y%m%d_%H%M%S")

        report_data = {
            "generated_at":  datetime.now().strftime("%d %B %Y, %I:%M %p"),
            "period":        f"Week of {datetime.now().strftime('%d %B %Y')}",
            "total_revenue": stats.get("total_revenue", 0),
            "total_orders":  stats.get("total_orders", 0),
            "impressions":   stats.get("impressions", 0),
            "clicks":        stats.get("clicks", 0),
            "conversion":    f"{(stats.get('total_orders',0)/max(stats.get('clicks',1),1)*100):.1f}%",
            "gig_stats":     stats.get("gig_stats", []),
            "recommendations": recs,
        }

        if PDF_AVAILABLE:
            path = self._build_pdf(report_data, ts)
        else:
            path = self._build_text_report(report_data, ts)

        logger.success(f"Fiverr report: {path}")
        return {"success": True, "report": report_data, "saved_at": path}

    def _build_pdf(self, data: dict, ts: str) -> str:
        """Real PDF with reportlab."""
        path = str(self.output_dir / f"fiverr_report_{ts}.pdf")
        doc  = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        story  = []

        # Title
        story.append(Paragraph(
            "🤖 ARIA — Fiverr Performance Report", styles['Title']
        ))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"Generated: {data['generated_at']}  |  Period: {data['period']}",
            styles['Normal']
        ))
        story.append(Spacer(1, 20))

        # Stats table
        story.append(Paragraph("📊 Performance Summary", styles['Heading2']))
        table_data = [
            ["Metric", "Value"],
            ["Total Revenue",  f"${data['total_revenue']}"],
            ["Total Orders",   str(data['total_orders'])],
            ["Impressions",    str(data['impressions'])],
            ["Clicks",         str(data['clicks'])],
            ["Conversion Rate", data['conversion']],
        ]
        tbl = Table(table_data, colWidths=[200, 200])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
            ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, 0), 12),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.HexColor('#F0F4F8'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',  (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 20))

        # Recommendations
        story.append(Paragraph("📌 Recommendations", styles['Heading2']))
        for rec in data['recommendations']:
            story.append(Paragraph(f"• {rec}", styles['Normal']))
            story.append(Spacer(1, 6))

        story.append(Spacer(1, 20))
        story.append(Paragraph(
            "Generated by ARIA — Your AI Personal Assistant",
            styles['Italic']
        ))

        doc.build(story)
        return path

    def _build_text_report(self, data: dict, ts: str) -> str:
        """Text fallback report (reportlab nahi hai to)."""
        path = str(self.output_dir / f"fiverr_report_{ts}.txt")
        lines = [
            "=" * 50,
            "ARIA — Fiverr Performance Report",
            "=" * 50,
            f"Generated : {data['generated_at']}",
            f"Period    : {data['period']}",
            "",
            "PERFORMANCE SUMMARY",
            "-" * 30,
            f"Revenue    : ${data['total_revenue']}",
            f"Orders     : {data['total_orders']}",
            f"Impressions: {data['impressions']}",
            f"Clicks     : {data['clicks']}",
            f"Conversion : {data['conversion']}",
            "",
            "RECOMMENDATIONS",
            "-" * 30,
        ] + [f"• {r}" for r in data['recommendations']] + [
            "",
            "Generated by ARIA — Your AI Personal Assistant",
            "=" * 50,
        ]
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        return path

    def _get_recommendations(self, stats: dict) -> list:
        recs   = []
        clicks = stats.get("clicks", 0)
        orders = stats.get("total_orders", 0)
        impr   = stats.get("impressions", 0)

        if impr > 0 and clicks / max(impr, 1) < 0.02:
            recs.append("CTR kam hai — thumbnail improve karo (bright colors, clear text)")
        if clicks > 0 and orders / max(clicks, 1) < 0.05:
            recs.append("Conversion low — pricing aur description review karo")
        if not recs:
            recs = [
                "Har hafta keywords refresh karo",
                "Response time 1 hour se kam rakhein",
                "Buyer Requests daily check karein",
                "Gig video add karo — conversions 200% badhti hain",
                "5-star reviews ke liye overdeliver karein",
            ]
        return recs
