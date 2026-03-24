# ============================================================
# ARIA Phase 3 — NLP Intents Patch
# All Phase 3 intents for master executor
# ============================================================

PHASE3_INTENTS = {
    # ── CV Manager ───────────────────────────────────────────
    "cv_build": [
        r"\b(cv|resume)\b.{0,20}\b(banao|create|scratch|likho|build)\b",
        r"\b(meri cv banao|create my resume|new cv)\b",
        r"\b(cv banao|resume banao)\b",
    ],
    "cv_improve": [
        r"\b(cv|resume)\b.{0,20}\b(improve|behtar|polish|update|fix)\b",
        r"\b(meri cv improve|cv ko better banao)\b",
    ],
    "cv_customize": [
        r"\b(cv|resume)\b.{0,30}\b(customize|is job ke liye|tailor|match)\b",
        r"\b(is job ke liye cv|job ke hisaab se cv)\b",
    ],
    "cv_ats_check": [
        r"\b(ats|applicant tracking|ats score)\b",
        r"\b(cv ka score|cv check karo|cv match)\b",
        r"\b(kya meri cv|is job ke liye theek)\b",
    ],
    "cover_letter": [
        r"\b(cover letter|covering letter)\b",
        r"\b(cover letter likho|covering letter banao)\b",
    ],
    "cv_versions": [
        r"\b(cv versions|saved cvs|meri cvs)\b",
        r"\b(cv list|cv files)\b",
    ],

    # ── Job Hunter ───────────────────────────────────────────
    "job_search": [
        r"\b(jobs|job)\b.{0,30}\b(dhoondo|search|find|talash)\b",
        r"\b(react jobs|python jobs|developer jobs)\b.{0,20}\b(dhoondo|find)\b",
        r"\b(salary|50k|100k)\b.{0,20}\b(jobs|job)\b",
        r"\b(linkedin|indeed|rozee)\b.{0,20}\b(jobs|search)\b",
    ],
    "job_apply": [
        r"\b(apply|application)\b.{0,30}\b(karo|submit|bhejo|do)\b",
        r"\b(is company mein apply|apply kar do|job apply)\b",
        r"\b(form fill|application submit)\b",
    ],
    "job_followup": [
        r"\b(follow up|followup)\b.{0,20}\b(job|application|apply)\b",
        r"\b(application follow up|job follow up karo)\b",
    ],
    "job_status": [
        r"\b(applications|application)\b.{0,20}\b(status|track|check)\b",
        r"\b(kitni applications|job tracker|applied jobs)\b",
    ],

    # ── Govt Opportunities ───────────────────────────────────
    "govt_opportunities": [
        r"\b(govt|government|sarkari)\b.{0,30}\b(scholarship|opportunity|job|scheme|program)\b",
        r"\b(scholarship|scholarships)\b.{0,20}\b(dhoondo|find|available|show)\b",
        r"\b(hec|fpsc|ppsc|nadra|ehsaas|pm youth|peef)\b",
        r"\b(new opportunities|latest scholarships|govt schemes)\b",
        r"\b(government ne|govt ki taraf se|sarkari)\b.{0,20}\b(koi|new|nai|scholarship|job)\b",
        r"\b(apply karna hai govt|government opportunity)\b",
        r"\b(international scholarship|chevening|fulbright|daad|commonwealth)\b",
    ],
    "govt_apply": [
        r"\b(govt|scholarship|sarkari)\b.{0,20}\b(apply|application)\b.{0,20}\b(karo|submit)\b",
        r"\b(is scholarship mein apply|govt job apply)\b",
        r"\b(apply kar do|apply karo)\b.{0,20}\b(scholarship|govt|sarkari)\b",
    ],

    # ── Social Media ─────────────────────────────────────────
    "content_create": [
        r"\b(content|video)\b.{0,20}\b(banao|create|banaoo)\b",
        r"\b(tutorial banao|blog video|aaj ki video)\b",
        r"\b(tiktok video|instagram reel|youtube video)\b.{0,20}\b(banao|create)\b",
        r"\b(aaj coding tutorial|video script)\b",
    ],
    "hashtags_generate": [
        r"\b(hashtags|hashtag)\b.{0,20}\b(do|generate|suggest|chahiye)\b",
        r"\b(30 hashtags|trending hashtags|best hashtags)\b",
    ],
    "trending_topics": [
        r"\b(trending|viral|kya trend)\b.{0,20}\b(topics|content|hai|hain)\b",
        r"\b(aaj kya trending|what is trending)\b",
    ],
    "content_calendar": [
        r"\b(content calendar|posting schedule|week ka plan)\b",
        r"\b(7 days|weekly content|content plan banao)\b",
    ],
    "caption_write": [
        r"\b(caption|captions)\b.{0,20}\b(likho|write|banao)\b",
        r"\b(instagram caption|tiktok caption|post caption)\b",
    ],
    "viral_score": [
        r"\b(viral|viral score|viral potential)\b",
        r"\b(kitna viral hoga|viral ho sakta hai)\b",
    ],
    "social_report": [
        r"\b(social media|growth)\b.{0,20}\b(report|stats|analytics)\b",
        r"\b(followers report|engagement report)\b",
    ],
    "competitor_social": [
        r"\b(competitor|competition)\b.{0,20}\b(account|tiktok|instagram|analyze)\b",
        r"\b(competitor ka account|rival account)\b",
    ],

    # ── Website Manager ──────────────────────────────────────
    "blog_write": [
        r"\b(blog|blog post|article)\b.{0,20}\b(likho|write|banao|create)\b",
        r"\b(website pe blog|seo blog|website post)\b",
        r"\b(react development ke barey|blog likhna hai)\b",
    ],
    "service_page": [
        r"\b(service page|services page)\b.{0,20}\b(add|banao|create)\b",
        r"\b(web development ka|service add karo)\b",
    ],
    "seo_check": [
        r"\b(seo|seo score|seo check)\b.{0,20}\b(check|score|karo)\b",
        r"\b(page ka seo|website seo|existing pages)\b",
    ],
    "git_push": [
        r"\b(git|github)\b.{0,20}\b(push|commit|upload)\b",
        r"\b(git push karo|code push karo|github pe upload)\b",
    ],
    "website_generate": [
        r"\b(website|web app)\b.{0,30}\b(banao|generate|create|build)\b",
        r"\b(react website|full stack website|dark theme website)\b",
        r"\b(client ke liye website|website code generate)\b",
    ],

    # ── Client Manager ───────────────────────────────────────
    "client_add": [
        r"\b(client|customer)\b.{0,20}\b(add|save|register|naya)\b",
        r"\b(naya client|new client add)\b",
    ],
    "client_status": [
        r"\b(\w+)\b.{0,15}\b(ka project|ka status|ki project)\b",
        r"\b(client status|project status|ahmed ka|sara ka)\b",
    ],
    "invoice_create": [
        r"\b(invoice|bill)\b.{0,20}\b(banao|create|generate)\b",
        r"\b(invoice generate|client ko bill|payment invoice)\b",
    ],
    "proposal_generate": [
        r"\b(proposal|contract|agreement)\b.{0,20}\b(likho|banao|generate)\b",
        r"\b(project proposal|client proposal|contract banao)\b",
    ],
    "payment_track": [
        r"\b(payment|paid|overdue)\b.{0,20}\b(track|check|status|mark)\b",
        r"\b(payment aya|invoice paid|overdue invoices)\b",
    ],
    "disk_cleanup": [
        r"\b(c drive|disk|storage)\b.{0,20}\b(clean|cleanup|saaf|free)\b",
        r"\b(c drive full|disk full|storage clean karo)\b",
        r"\b(laptop clean|temp files|cache clear)\b",
    ],
}


def patch_phase3_intents(nlp_engine):
    """Phase 3 intents NLP engine mein add karo."""
    for intent, patterns in PHASE3_INTENTS.items():
        nlp_engine.intent_patterns[intent] = patterns
    total = len(nlp_engine.intent_patterns)
    import logging
    logging.info(f"Phase 3 intents added — Total: {total}")
    return nlp_engine
