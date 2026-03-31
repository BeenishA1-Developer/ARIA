# ============================================================
# ARIA Blogging Agent - Web Server (Flask)
# ============================================================
import os, sys, json, threading
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from core.competitor import CompetitorResearcher
from core.seo_writer  import SEOWriter
from core.poster      import WPPoster
from core.status_reporter import reporter
from config           import GROQ_API_KEY

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

GROQ_MODEL = "llama-3.3-70b-versatile"

app = Flask(__name__, static_folder="web")

# ── Persistent Data Helpers ─────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

def save_json(name, data):
    with open(DATA_DIR / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(name, default):
    path = DATA_DIR / f"{name}.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return default

def update_env(updates: dict):
    env_path = Path(__file__).parent / ".env"
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
    
    new_lines = []
    keys_updated = []
    for line in lines:
        matched = False
        for k, v in updates.items():
            if line.startswith(f"{k}="):
                new_lines.append(f"{k}={v}\n")
                keys_updated.append(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)
    
    for k, v in updates.items():
        if k not in keys_updated:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    load_dotenv(env_path, override=True)

# ── Global State ────────────────────────────────────────────
profile = load_json("profile", {
    "url": os.getenv("BLOG_URL", ""),
    "niche": os.getenv("BLOG_NICHE", ""),
})
history = load_json("chat_history", [])
keywords_cache = load_json("keywords", [])

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_AVAILABLE and GROQ_API_KEY else None
researcher = CompetitorResearcher()
writer     = SEOWriter()
poster     = WPPoster()

# ── AI Chat & Action Discovery ─────────────────────────────
def detect_intent(user_msg: str) -> dict:
    """Use AI to find what the user really wants to do."""
    if not groq_client: return {"action": "chat"}
    
    prompt = f"""
    Analyze the user's message and current context to detect intent.
    User Message: "{user_msg}"
    
    Context:
    - WP Connected: {poster.is_connected}
    - Keywords found: {len(keywords_cache)}
    - Site URL: {profile['url']}
    
    Valid Actions:
    1. "research": User wants to find keywords, analyze competitors, or research a niche.
    2. "write_post": User wants to write a blog post (possibly post it too). 
    3. "connect_wp": User wants to setup or connect WordPress.
    4. "chat": General talk or SEO advice.
    
    Return JSON only:
    {{"intent": "action_name", "reason": "why this action", "confidence": 0.0-1.0}}
    """
    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except:
        return {"intent": "chat"}

def ai_chat(user_msg: str, intent: str = "chat") -> str:
    if not groq_client:
        return "❌ Groq API key missing in .env!"

    system = f"""You are ARIA, a PRO AI Blogging Manager.
    Your goal is to help the user grow their blog through SEO and automation.

    CURRENT INTENT: {intent}

    INSTRUCTIONS:
    - If intent is 'research', state that you are NOW starting deep competitor analysis in the background. DO NOT claim it is finished.
    - If intent is 'write_post', state that you are NOW starting to write a 1500-word SEO blog. Warn the user that this will take about 30 seconds to complete in the background.
    - If intent is 'connect_wp', tell them to click the 'Settings' gear icon at the top right to enter their WordPress/Admin credentials.
    - If intent is 'chat', give expert blogging tips as a mentor.
    
    CRITICAL: Current action is JUST STARTING. Never say "I have uploaded" or "Research is complete" in your chat response. Use: "Main abhi shuru kar rahi hun...", "Thoda wait karein...", etc.
    
    Respond in the SAME language as the user (Urdu/English mix).
    Today: {datetime.now().strftime('%B %d, %Y')}
    """

    msgs = [{"role": "system", "content": system}]
    for h in history[-10:]: msgs.append(h)
    msgs.append({"role": "user", "content": user_msg})

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL, messages=msgs, max_tokens=1000
        )
        reply = resp.choices[0].message.content
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})
        save_json("chat_history", history[-50:])
        return reply
    except Exception as e:
        return f"❌ AI Error: {e}"

import schedule, time

# ── Daily Scheduler ─────────────────────────────────────────
def daily_task():
    """Runs research and post automatically every 24 hours."""
    logger.info("🕒 Daily task started: Researching & Posting...")
    reporter.info("🕒 Daily automation starting: Research & Posting...")
    
    # 1. Research
    if profile.get("url"):
        global keywords_cache
        keywords_cache = researcher.full_research(profile["url"], profile.get("niche", "scholarships"))
        save_json("keywords", keywords_cache)
    
    # 2. Write & Post
    kw = keywords_cache[0] if keywords_cache else {
        "keyword": profile.get("niche", "scholarships"),
        "target_title": f"Fully Funded Scholarships for International Students {datetime.now().year}"
    }
    article = writer.generate_full_article(kw)
    if article.get("success"):
        poster.post_to_wordpress(article)
        if keywords_cache: 
            keywords_cache.pop(0)
            save_json("keywords", keywords_cache)
    
    reporter.success("✅ Daily task completed!")

def run_scheduler():
    schedule.every().day.at("10:00").do(daily_task)
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# ── Routes ───────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global profile, keywords_cache
    data = request.json
    msg  = data.get("message", "")

    # Handle URL automatically
    if "https://" in msg and profile["url"] == "":
        profile["url"] = re.findall(r'https?://[^\s]+', msg)[0]
        save_json("profile", profile)

    # Detect AI Intent
    intent_data = detect_intent(msg)
    intent = intent_data.get("intent", "chat")

    # Get AI reply
    ai_reply = ai_chat(msg, intent)

    # Actions based on intent
    action_result = None
    
    if intent == "research":
        action_result = {"type": "research", "msg": "🔍 Researching competitors for you..."}
        def do_res():
            global keywords_cache
            keywords_cache = researcher.full_research(profile["url"], profile.get("niche", "scholarships"))
            save_json("keywords", keywords_cache)
            # Update chat history
            history.append({"role": "assistant", "content": f"✅ **Research Complete!**\n\nAb mere paas is topic se related {len(keywords_cache)} trending keywords hain. Kya main in par writing shuru karun?"})
            save_json("chat_history", history[-50:])
        threading.Thread(target=do_res, daemon=True).start()


    elif intent == "write_post":
        action_result = {"type": "writing", "msg": "✍️ Writing SEO-optimized post now..."}
        def do_write():
            kw = keywords_cache[0] if keywords_cache else {
                "keyword": profile.get("niche", "scholarships"),
                "target_title": f"International Scholarships for 2026: The Ultimate Guide"
            }
            article = writer.generate_full_article(kw)
            if article.get("success"):
                res = poster.post_to_wordpress(article)
                if keywords_cache: 
                    keywords_cache.pop(0)
                    save_json("keywords", keywords_cache)
                
                # Update chat history for the user to see
                result_msg = f"✅ **Post Published Successfully!**\n\n**Title:** {article['title']}\n"
                if res.get("success"):
                    link = res.get("link", f"{profile.get('url')}scholarship.php")
                    result_msg += f"🔗 **Live Link:** {link}\n\nAap is link par ja kar check kar sakti hain. Post successfully live ho chuki hai."
                else:
                    result_msg += f"⚠️ Website connected nahi thi, isliye post ko `outputs/` folder mein save kar diya gaya hai."
                
                history.append({"role": "assistant", "content": result_msg})
                save_json("chat_history", history[-50:])

        threading.Thread(target=do_write, daemon=True).start()


    elif intent == "connect_wp":
        action_result = {"type": "setup_wp", "msg": "Opening Settings portal..."}

    return jsonify({
        "reply": ai_reply,
        "action": action_result,
        "keywords": keywords_cache[:5],
        "profile": profile,
        "intent": intent_data
    })


@app.route("/settings", methods=["POST"])
def update_settings():
    data = request.json
    updates = {}
    if "wp_url" in data: updates["BLOG_URL"] = data["wp_url"]
    if "wp_user" in data: updates["WP_USER"] = data["wp_user"]
    if "wp_pass" in data: updates["WP_PASS"] = data["wp_pass"]
    
    if updates:
        update_env(updates)
        # Re-init poster and researcher
        global poster, profile
        poster = WPPoster()
        profile["url"] = data.get("wp_url", profile["url"])
        save_json("profile", profile)
        return jsonify({"success": True, "connected": poster.is_connected})
    return jsonify({"success": False})

@app.route("/keywords")
def get_keywords():
    return jsonify({"keywords": keywords_cache})

@app.route("/logs")
def get_logs():
    return jsonify({"logs": reporter.get_logs()})

@app.route("/history")
def get_history():
    return jsonify({"history": history})

@app.route("/status")
def status():
    outputs = Path(__file__).parent / "outputs"
    blogs = list(outputs.glob("*.html")) if outputs.exists() else []
    return jsonify({
        "profile": profile,
        "keywords_found": len(keywords_cache),
        "blogs_written": len(blogs),
        "wp_connected": poster.is_connected,
        "groq_ready": GROQ_AVAILABLE and bool(GROQ_API_KEY)
    })

if __name__ == "__main__":
    print("\n🚀 ARIA Blogging Agent Web UI starting...")
    print("📱 Browser mein kholein: http://localhost:5000")
    print("   (Ctrl+C se band karein)\n")
    import webbrowser
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
