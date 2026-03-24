# ============================================================
# ARIA — NLP Engine v2 (COMPLETE — 55+ intents)
# Urdu + English + Roman Urdu
# ============================================================

import re
from loguru import logger


class NLPEngine:
    """
    55+ intents — Phase 1 + Phase 2 complete.
    """

    def __init__(self):
        self.intent_patterns = self._build_all_intents()
        total = len(self.intent_patterns)
        logger.info(f"NLP Engine v2 — {total} intents loaded")

    def _build_all_intents(self) -> dict:
        return {
            # ══ PHASE 1 INTENTS ══════════════════════════════

            "greeting": [
                r"\b(hello|hi|hey|salam|assalam|aria|start)\b",
                r"\b(good morning|good evening|subah|shukriya)\b",
                r"\b(kya haal|kaisa ho|theek ho)\b",
            ],
            "screenshot": [
                r"\b(screenshot|screen shot|screen capture|capture screen)\b",
                r"\b(screen lo|screenshot lo|screen lelo)\b",
            ],
            "screenshot_scheduled": [
                r"\bscreenshot har\b",
                r"\bhar .{0,15} min.{0,5} (lo|screenshot)\b",
                r"\b(scheduled|automatic|auto)\b.{0,20}\b(screenshot|screen)\b",
                r"\b(screenshot)\b.{0,20}\b(schedule|automatically|har|every)\b",
                r"\b(har ghante|every hour|regular)\b.{0,20}\b(screenshot)\b",
            ],
            "diagnostics": [
                r"\b(diagnostics|health check|system check|test karo)\b",
                r"\b(sab kuch|all systems|complete check)\b.{0,20}\b(check|test)\b",
                r"\b(aria)\b.{0,15}\b(theek|working|chal rahi)\b",
            ],
            "file_search": [
                r"\b(find|search|dhoondo|dhundho|locate|talash)\b.{0,30}\b(file|folder|document|pdf|image|photo|video)\b",
                r"\b(file|document|pdf)\b.{0,30}\b(dhoondo|find|kahan|where)\b",
                r"\b(meri|mera|mujhe).{0,20}(file|pdf|document)\b",
            ],
            "file_organize": [
                r"\b(organize|sort|arrange|clean|tartib)\b.{0,30}\b(folder|files|downloads|desktop)\b",
                r"\b(downloads|desktop).{0,20}(organize|clean|sort)\b",
            ],
            "app_open": [
                r"\b(open|kholo|launch|start)\b.{0,30}\b(chrome|firefox|notepad|excel|word|vlc|spotify|code|vscode|calculator|paint)\b",
                r"\b(chrome|firefox|notepad|excel|vlc|spotify|vscode|calculator)\b.{0,20}\b(kholo|open|chalaoo)\b",
            ],
            "app_close": [
                r"\b(close|band|quit|exit)\b.{0,30}\b(chrome|firefox|notepad|excel|word|vlc|app)\b",
                r"\b(band karo|close karo|quit karo)\b",
            ],
            "system_status": [
                r"\b(system status|system info|cpu|ram|battery|disk|memory)\b",
                r"\b(laptop ka status|computer status|performance)\b",
                r"\b(kitni battery|ram kitni|cpu kitna|disk space)\b",
            ],
            "email_draft": [
                r"\b(email|mail)\b.{0,40}\b(likho|draft|compose|write|banao)\b",
                r"\b(likho|write|draft)\b.{0,40}\b(email|mail)\b",
                r"\b(ko email|ko mail)\b",
            ],
            "pdf_merge": [
                r"\b(pdf|pdfs)\b.{0,30}\b(merge|combine|jodo|mila)\b",
            ],
            "find_duplicates": [
                r"\b(duplicate|copy|copies)\b.{0,30}\b(file|files|find|dhoondo)\b",
            ],
            "file_create": [
                r"\b(create|banao|make|new)\b.{0,30}\b(file|folder|directory)\b",
                r"\b(new folder|naya folder)\b",
            ],
            "volume_control": [
                r"\b(volume|sound|awaaz)\b.{0,30}\b(up|down|increase|decrease|mute|barhao|ghatao)\b",
            ],
            "time_date": [
                r"\b(time|waqt|date|tarikh|day|clock)\b",
                r"\b(abhi kitne baje|kya time|kitni taarikh)\b",
            ],
            "help": [
                r"\b(help|madad|guide|commands|kya kar sakte)\b",
                r"\b(kya kya kar sakti|what can you do)\b",
            ],
            "stop": [
                r"\b(stop|exit|quit|band ho jao|rukk|bye|goodbye|khuda hafiz)\b",
                r"\b(aria band|aria stop|shut down)\b",
            ],

            # ══ PHASE 2 INTENTS ══════════════════════════════

            # WhatsApp
            "whatsapp_send": [
                r"\b(whatsapp|wa)\b.{0,30}\b(bhejo|send|message)\b",
                r"\b(0\d{10})\b.{0,20}\b(message|text|whatsapp)\b",
                r"\b(message bhejo|msg bhejo)\b",
                r"\bwhatsapp pe\b",
            ],
            "whatsapp_bulk": [
                r"\b(sab|all|bulk)\b.{0,20}\b(clients|contacts|logo)\b.{0,20}\b(whatsapp|message)\b",
                r"\b(bulk|mass)\b.{0,20}\b(message|whatsapp|send)\b",
                r"\b(sab clients ko|all clients)\b.{0,20}\b(bhejo|send)\b",
            ],

            # Gmail Phase 2
            "email_send_now": [
                r"\b(email|mail)\b.{0,30}\b(bhejo|send|bhejna)\b",
                r"\b(bhejo)\b.{0,30}\b(email|mail)\b",
            ],
            "inbox_check": [
                r"\b(inbox|emails)\b.{0,20}\b(check|dekho|batao|show)\b",
                r"\b(inbox check|mail check|emails dekho)\b",
                r"\b(naye emails|unread|new mail)\b",
            ],
            "email_reply": [
                r"\b(reply likho|reply karo|jawab do)\b",
                r"\b(reply|jawab|response)\b.{0,20}\b(email|mail)\b",
                r"\b(email ka reply|mail ka jawab)\b",
                r"\b(is email ko reply)\b",
            ],
            "email_search": [
                r"\b(email|mail)\b.{0,30}\b(dhoondo|search|find|talash)\b",
                r"\b(ahmed ki email|client ki mail)\b",
                r"\b(dhoondo|find)\b.{0,20}\b(email|mail)\b.{0,20}\b(by|from|se)\b",
            ],

            # File send
            "file_send": [
                r"\b(cv|pdf|document|file).{0,10}(email|whatsapp).{0,10}(bhejo|send)\b",
                r"\b(file|pdf|cv|resume|document)\b.{0,30}\b(bhejo|send|email|whatsapp)\b",
                r"\b(bhejo|send)\b.{0,30}\b(file|pdf|document|folder)\b",
                r"\b(cv|resume).{0,20}(bhejo|send)\b",
            ],
            "folder_send": [
                r"\b(folder|project)\b.{0,20}\b(email|zip|bhejo|send)\b",
                r"\b(zip karke bhejo|folder email karo)\b",
            ],

            # Fiverr — ALL sub-intents
            "fiverr_keywords": [
                r"\b(fiverr|gig)\b.{0,30}\b(keywords|keyword)\b",
                r"\b(keywords)\b.{0,20}\b(do|dono|generate|chahiye|fiverr)\b",
                r"\b(fiverr seo|gig seo)\b",
            ],
            "fiverr_keyword_frequency": [
                r"\b(keyword frequency|keywords kitni baar|how often keywords)\b",
                r"\b(frequency analyzer|keyword count|analyze keywords)\b",
                r"\b(competitor keywords analyze|titles analyze)\b",
            ],
            "fiverr_ranking": [
                r"\b(ranking|rank)\b.{0,30}\b(opportunity|chance|kahan|fiverr)\b",
                r"\b(page 1|first page)\b.{0,20}\b(fiverr|rank)\b",
                r"\b(ranking opportunity|rank kahan)\b",
            ],
            "fiverr_title": [
                r"\b(gig title|title)\b.{0,20}\b(optimize|improve|better|behtar)\b",
                r"\b(mera gig title|my gig title)\b.{0,20}\b(optimize|fix|improve)\b",
            ],
            "fiverr_tags": [
                r"\b(tags|tag)\b.{0,20}\b(suggest|do|generate|fiverr)\b",
                r"\b(30 tags|fiverr tags|gig tags)\b",
                r"\b(tags generate|tags suggest)\b",
            ],
            "fiverr_description": [
                r"\b(description|desc)\b.{0,20}\b(improve|enhance|better|optimize)\b",
                r"\b(gig description|mera description)\b.{0,20}\b(improve|fix)\b",
            ],
            "fiverr_competitor": [
                r"\b(competitor|competition)\b.{0,20}\b(analyze|check|fiverr)\b",
                r"\b(fiverr).{0,20}(analyze|analysis|competitor)\b",
            ],
            "fiverr_pricing": [
                r"\b(pricing|price|rate)\b.{0,20}\b(strategy|fiverr|suggest|kya rakhun)\b",
                r"\b(basic standard premium|packages)\b.{0,20}\b(fiverr|price)\b",
            ],
            "fiverr_report": [
                r"\b(fiverr|performance)\b.{0,30}\b(report|stats|analytics)\b",
                r"\b(weekly|monthly)\b.{0,20}\b(report|performance)\b",
            ],

            # Task Scheduler
            "schedule_task": [
                r"\b(schedule|kal|tomorrow|baad|later)\b.{0,40}\b(email|message|task|karo)\b",
                r"\b(subah|morning|evening|shaam)\b.{0,30}\b(email|message|bhejo)\b",
                r"\b(har|every|daily|weekly|monday)\b.{0,30}\b(karo|report|email)\b",
                r"\b(har|every)\b.{0,20}\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
                r"\b(schedule karo|schedule kar)\b",
                r"\b(automatically|auto|recurring)\b.{0,20}\b(karo|run|bhejo)\b",
            ],
        }

    def detect_intent(self, text: str) -> dict:
        text_lower = text.lower().strip()
        best_intent = "unknown"
        best_score  = 0.0

        for intent, patterns in self.intent_patterns.items():
            score = sum(
                1 for p in patterns
                if re.search(p, text_lower, re.IGNORECASE)
            )
            normalized = score / len(patterns)
            if normalized > best_score:
                best_score  = normalized
                best_intent = intent

        entities = self._extract_entities(text_lower)
        result   = {
            "intent":        best_intent,
            "confidence":    round(best_score, 2),
            "entities":      entities,
            "original_text": text,
            "language":      self._detect_language(text),
        }
        logger.debug(f"Intent: {best_intent} ({best_score:.2f})")
        return result

    def _extract_entities(self, text: str) -> dict:
        entities = {}

        # Recipient name (email/whatsapp)
        m = re.search(
            r'(\w+)\s+(?:ko|ke liye|for)\s+.*?(?:email|mail|message|whatsapp)',
            text, re.IGNORECASE
        )
        if m:
            entities["recipient"] = m.group(1).capitalize()

        # File name
        m = re.search(r'(\w+\.\w{2,4})', text)
        if m:
            entities["filename"] = m.group(1)

        # App name
        for app in ["chrome","firefox","notepad","excel","word",
                    "vlc","spotify","vscode","calculator","paint"]:
            if app in text:
                entities["app_name"] = app
                break

        # Folder
        for folder in ["downloads","desktop","documents",
                       "pictures","videos","music"]:
            if folder in text:
                entities["folder"] = folder
                break

        # Pakistani phone
        m = re.search(r'\b(0\d{10}|\+92\d{10})\b', text)
        if m:
            entities["phone"] = m.group(1)

        # Fiverr category
        fiverr_triggers = ["keywords","tags","title","description",
                           "gig","fiverr","competitor","report","pricing"]
        if any(t in text for t in fiverr_triggers):
            skip = {"fiverr","gig","keywords","tags","title",
                    "description","do","karo","chahiye","report",
                    "competitor","analyze","pricing","strategy"}
            words = [w for w in text.split()
                     if len(w) > 2 and w not in skip]
            if words:
                entities["fiverr_category"] = " ".join(words[:3])

        return entities

    def _detect_language(self, text: str) -> str:
        if len(re.findall(r'[\u0600-\u06FF]', text)) > 2:
            return "urdu"
        roman = ["karo","karta","hai","hain","mera","meri","tumhara",
                 "bhejo","dhoondo","kholo","banao","likho","batao","lo"]
        if sum(1 for w in roman if w in text.lower()) >= 2:
            return "roman_urdu"
        return "english"


# ── Phase 2 intents already included above ───────────────────
# (kept as stub for backward compat)
def _patch_phase2_intents(nlp_engine):
    """No-op — Phase 2 intents already in NLPEngine v2."""
    return nlp_engine


# ── PHASE 3 INTENTS — add to NLPEngine at runtime ────────────

PHASE3_INTENTS = {
    # CV Manager
    "cv_create":     [r"\b(cv|resume)\b.{0,20}\b(banao|create|banaoo|scratch)\b",
                      r"\b(meri cv banao|naya cv|new resume)\b"],
    "cv_improve":    [r"\b(cv|resume)\b.{0,20}\b(improve|better|polish|enhance|update)\b",
                      r"\b(cv improve|resume improve)\b"],
    "cv_customize":  [r"\b(cv|resume)\b.{0,30}\b(customize|tailor|is job ke liye)\b",
                      r"\b(is job ke liye cv|job ke liye resume)\b"],
    "cv_ats":        [r"\b(ats|score)\b.{0,20}\b(check|test|cv|resume)\b",
                      r"\b(cv ka ats|ats score check)\b"],
    "cv_match":      [r"\b(cv|resume)\b.{0,30}\b(match|fit|is job ke liye theek)\b",
                      r"\b(kya meri cv|job ke liye theek)\b"],
    "cv_pdf":        [r"\b(cv|resume)\b.{0,20}\b(pdf|download|generate|banao)\b",
                      r"\b(cv pdf download|resume pdf)\b"],

    # Job Hunter
    "job_search":    [r"\b(jobs|job)\b.{0,30}\b(dhoondo|search|find|chahiye)\b",
                      r"\b(react developer jobs|python jobs|web developer jobs)\b",
                      r"\bsalary.{0,20}jobs\b"],
    "job_apply":     [r"\b(apply karo|apply|application)\b.{0,30}\b(job|company|position)\b",
                      r"\b(is company mein apply|job apply)\b",
                      r"\b(auto apply|automatically apply)\b"],
    "job_status":    [r"\b(application|apply)\b.{0,20}\b(status|track|kahan)\b",
                      r"\b(kaunse jobs apply|applications status)\b"],
    "cover_letter":  [r"\b(cover letter|covering letter)\b.{0,20}\b(likho|banao|create)\b",
                      r"\b(cover letter chahiye|application letter)\b"],
    "job_alert":     [r"\b(daily alert|job alert|notification)\b.{0,20}\b(set|lagao)\b",
                      r"\b(roz jobs batao|daily job update)\b"],

    # Govt Opportunities — NEW FEATURE
    "govt_search":   [r"\b(govt|government|sarkari)\b.{0,30}\b(scholarship|job|opportunity|program)\b",
                      r"\b(scholarship dhoondo|govt jobs|sarkari naukri)\b",
                      r"\b(hec|fpsc|ppsc|nts|peef)\b.{0,20}\b(scholarship|job|latest)\b",
                      r"\b(latest scholarship|new scholarship|apply scholarship)\b",
                      r"\b(govt ki taraf|government ne)\b.{0,30}\b(scholarship|program|launch)\b",
                      r"\b(koi nayi opportunity|new govt program|sarkari scholarship)\b"],

    # Social Media
    "social_content":   [r"\b(video|content)\b.{0,30}\b(banao|create|script)\b",
                          r"\b(tiktok|instagram|youtube)\b.{0,20}\b(video|content|post)\b",
                          r"\b(coding tutorial banao|tutorial video)\b"],
    "social_hashtags":  [r"\b(hashtags|tags)\b.{0,20}\b(do|generate|social media)\b",
                          r"\b(30 hashtags|hashtags chahiye)\b"],
    "social_calendar":  [r"\b(content calendar|posting schedule|7 days|week)\b.{0,20}\b(content|plan)\b"],
    "social_viral":     [r"\b(viral|potential|score)\b.{0,20}\b(check|video|content)\b",
                          r"\b(viral potential|kitna viral)\b"],
    "social_trends":    [r"\b(trends|trending|kya chal raha)\b.{0,20}\b(social|tiktok|instagram)\b"],
    "social_hooks":     [r"\b(hook|first 3 second|opening line)\b",
                          r"\b(hook ideas|viral hook)\b"],
    "social_report":    [r"\b(social media|growth)\b.{0,20}\b(report|analytics|stats)\b"],

    # Website
    "website_generate": [r"\b(website|app)\b.{0,30}\b(banao|create|generate|code)\b",
                          r"\b(react website|nextjs|html website)\b.{0,20}\b(banao|create)\b",
                          r"\b(full stack website|complete website)\b"],
    "website_blog":     [r"\b(blog|seo post|article)\b.{0,30}\b(likho|website pe|add)\b",
                          r"\b(website pe blog|seo blog|website content)\b"],
    "website_seo":      [r"\b(seo score|seo check)\b.{0,20}\b(website|page)\b",
                          r"\b(page ka seo|website seo analyze)\b"],

    # Client Manager
    "client_add":      [r"\b(client|customer)\b.{0,20}\b(add|register|save)\b",
                         r"\b(naya client|client add karo)\b"],
    "client_status":   [r"\b(client|ahmed|sara)\b.{0,30}\b(status|project|kya chal)\b",
                         r"\b(ka project status|client ka kaam)\b"],
    "invoice_create":  [r"\b(invoice|bill)\b.{0,20}\b(banao|create|generate)\b",
                         r"\b(invoice chahiye|client ko bill)\b"],
    "payment_record":  [r"\b(payment|paisa)\b.{0,20}\b(mila|received|record|aa gaya)\b",
                         r"\b(payment record|paisa mila)\b"],
    "proposal_create": [r"\b(proposal|quote|quotation)\b.{0,20}\b(banao|create|bhejo)\b"],
    "laptop_cleanup":  [r"\b(laptop|c drive|storage)\b.{0,20}\b(clean|full|space|analyze)\b",
                         r"\b(c drive full|storage kam|disk space)\b"],
}
