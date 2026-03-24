# ============================================================
# ARIA Phase 3 — NLP Intent Patch (adds to NLPEngine)
# ============================================================

PHASE3_INTENTS = {
    # CV Manager
    "cv_create":       [r"\b(meri cv banao|create cv|cv banao|resume banao)\b"],
    "cv_improve":      [r"\b(cv improve|cv better|cv fix|cv polish)\b"],
    "cv_customize":    [r"\b(cv customize|is job ke liye cv|cv tailor)\b",
                        r"\b(cv ko update karo is job ke liye)\b"],
    "cv_ats_check":    [r"\b(ats score|cv score|cv check|keyword match)\b"],
    "cv_versions":     [r"\b(cv versions|meri sab cvs|cv list)\b"],
    "cv_save":         [r"\b(cv save|meri cv store|cv upload)\b"],
    "cover_letter":    [r"\b(cover letter|covering letter)\b"],

    # Job Search
    "job_search":      [r"\b(jobs dhoondo|find jobs|react jobs|developer jobs|jobs search)\b",
                        r"\b(salary .{0,20} jobs|remote jobs|pakistan jobs)\b"],
    "job_analyze":     [r"\b(job description analyze|jd analyze|is job ka analysis)\b"],
    "job_apply":       [r"\b(is company mein apply|job apply|apply karo)\b",
                        r"\b(apply workflow|full apply)\b"],
    "application_status": [r"\b(application status|meri applications|applied jobs)\b",
                            r"\b(follow up|followup).{0,20}(job|application)\b"],

    # Opportunities (NEW FEATURE)
    "find_opportunities": [
        r"\b(scholarship|scholarships|wazifa|wazaif)\b",
        r"\b(govt.{0,20}(opportunity|opportunities|scheme|program))\b",
        r"\b(hec|pmyp|ehsaas|bisp|fpsc|nts)\b",
        r"\b(new scholarship|latest scholarship|apply scholarship)\b",
        r"\b(govt ne.{0,30}(show|announce|nikali))\b",
        r"\b(laptop scheme|pm laptop|pm scholarship)\b",
        r"\b(fully funded|international scholarship|chevening|fulbright|erasmus)\b",
        r"\b(govt job|sarkari naukri|government job)\b",
        r"\b(opportunities dhoondo|find opportunities|nayi opportunities)\b",
    ],
    "check_eligibility":  [r"\b(kya main eligible|eligibility check|am i eligible)\b"],
    "prepare_application":[r"\b(application tayyar|prepare application|apply guide)\b"],

    # Social Media
    "content_create":   [r"\b(content banao|video banao|post banao|tutorial banao)\b",
                         r"\b(aaj.{0,20}(tiktok|instagram|youtube|video))\b"],
    "hashtags_gen":     [r"\b(hashtags do|hashtag generate|30 hashtags)\b"],
    "hook_ideas":       [r"\b(hook|first 3 seconds|scroll stop|catchy)\b"],
    "content_calendar": [r"\b(content calendar|week ka plan|content plan)\b",
                         r"\b(puri week|7 days content)\b"],
    "trending_topics":  [r"\b(trending|kya trend|viral topics|what is trending)\b"],
    "viral_score":      [r"\b(viral score|viral potential|kitna viral)\b"],
    "competitor_sm":    [r"\b(competitor analyze|account analyze|@\w+.{0,20}analyze)\b"],
    "sm_report":        [r"\b(social media report|growth report|follower report)\b"],

    # Website
    "website_blog":     [r"\b(blog likho|blog post|seo blog|website pe post)\b"],
    "website_service":  [r"\b(service page|website page banao)\b"],
    "website_seo":      [r"\b(seo check|seo score|page seo|website seo)\b"],
    "website_generate": [r"\b(website banao|react website|full website code)\b",
                         r"\b(node backend|express backend)\b"],
    "git_push":         [r"\b(git push|commit push|code push)\b"],
    "sitemap_update":   [r"\b(sitemap|sitemap update)\b"],

    # Client Management
    "client_status":    [r"\b(\w+)\s+ka\s+project\s+status\b",
                         r"\b(client status|project status|kaam status)\b"],
    "client_add":       [r"\b(client add|naya client|add client)\b"],
    "invoice_generate": [r"\b(invoice banao|invoice generate|bill banao)\b"],
    "proposal_generate":[r"\b(proposal banao|project proposal)\b"],
    "overdue_payments": [r"\b(overdue|payment pending|paise baki|unpaid)\b"],

    # Laptop
    "laptop_analyze":   [r"\b(c drive|laptop storage|disk full|space kam)\b",
                         r"\b(laptop analyze|storage analyze|kitni space)\b"],
    "laptop_cleanup":   [r"\b(laptop clean|c drive clean|temp files|cache clear)\b",
                         r"\b(space free|storage free)\b"],
    "large_files":      [r"\b(large files|bari files|big files dhoondo)\b"],
}


def patch_phase3_intents(nlp_engine):
    """Phase 3 intents NLPEngine mein add karo."""
    for intent, patterns in PHASE3_INTENTS.items():
        nlp_engine.intent_patterns[intent] = patterns
    logger.msg = f"Phase 3: {len(PHASE3_INTENTS)} intents added"
    return nlp_engine

try:
    from loguru import logger
except ImportError:
    class logger:
        @staticmethod
        def info(m): print(m)
