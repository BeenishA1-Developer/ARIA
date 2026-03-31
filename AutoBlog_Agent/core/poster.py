# ============================================================
# ARIA Pro Agent - Multi-Platform Poster
# ============================================================
import os, requests, base64, json, re, threading
from datetime import datetime
from loguru import logger
from core.status_reporter import reporter

def send_notification(msg, phone):
    """Sends a notification (WhatsApp/SMS placeholder)."""
    # Logic for Twilio or simple logger
    logger.info(f"NOTIFICATION: Sending to {phone} -> {msg}")
    # In a real scenario, use:
    # client = Client(SID, TOKEN)
    # client.messages.create(to=phone, from_=FROM, body=msg)
    reporter.info(f"📲 Notification bheji gayi: {phone}")

class WPPoster:
    """Enhanced poster for WordPress AND Custom PHP sites."""

    def __init__(self, config=None):
        self.config = config or {
            "url": os.getenv("BLOG_URL", ""),
            "user": os.getenv("WP_USER", ""),
            "pass": os.getenv("WP_PASS", ""),
            "phone": os.getenv("PHONE", "03156284538")
        }
        self.session = requests.Session()
        self.is_connected = False
        self._detect_and_connect()

    def _detect_and_connect(self):
        url = self.config.get("url", "").rstrip('/')
        if not url: return

        # Check if WordPress
        if "wp-json" in url:
            self.type = "wordpress"
            self._verify_wp()
        else:
            self.type = "custom_php"
            self._verify_custom()

    def _verify_wp(self):
        url = self.config.get("url", "").rstrip('/')
        user, pwd = self.config.get("user"), self.config.get("pass")
        auth = base64.b64encode(f"{user}:{pwd}".encode()).decode()
        headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}
        try:
            r = requests.get(f"{url}/wp-json/wp/v2/users/me", headers=headers, timeout=10)
            self.is_connected = (r.status_code == 200)
        except: pass

    def _verify_custom(self):
        url = self.config.get("url", "").rstrip('/')
        user, pwd = self.config.get("user"), self.config.get("pass")
        login_url = f"{url}/admin/login.php"
        try:
            r = self.session.post(login_url, data={"username": user, "password": pwd}, timeout=15)
            # If dashboard appears, success
            self.is_connected = ("dashboard" in r.text.lower() or "logout" in r.text.lower() or r.status_code == 200)
            if self.is_connected: logger.success("Connected to Custom Admin!")
        except Exception as e:
            logger.error(f"Custom Login Failed: {e}")

    def post_to_wordpress(self, data, status="publish"):
        """Main entry point for posting."""
        if not self.is_connected:
            return self._save_local(data)
        
        if self.type == "wordpress":
            return self._do_post_wp(data, status)
        else:
            return self._do_post_custom(data, status)

    def _do_post_custom(self, data, status="publish"):
        url = self.config.get("url", "").rstrip('/')
        add_url = f"{url}/admin/scholarships.php?action=add"
        
        title = data.get("title", "Scholarship Today")
        # Creating a slug like a typical PHP site: lower + hyphen
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        
        payload = {
            "title": title,
            "category_id": 1,
            "country": data.get("country", "Various Countries"), 
            "level": "BS/MS/PhD",
            "funding_type": "Fully Funded",
            "host_university": "Multiple Universities",
            "deadline": datetime.now().strftime("%Y-12-31"),
            "amount": "Full Living/Tuition",
            "official_link": "https://scholarshipsguide.xyz",
            "status": status,
            "benefits": data.get("content", ""),
            "eligibility": "Available for Pakistani students.",
            "how_to_apply": "Complete details are on the official link.",
            "meta_title": title,
            "meta_description": data.get("meta_description", ""),
            "meta_keywords": "scholarships, study abroad, " + title,
            "submit": "Add Scholarship"
        }
        
        try:
            r = self.session.post(add_url, data=payload, timeout=20)
            if r.status_code == 200:
                final_link = f"{url}/scholarship.php?slug={slug}"
                reporter.success(f"🚀 Published! Link: {final_link}")
                send_notification(f"Published: {title} at {final_link}", self.config.get('phone'))
                return {"success": True, "link": final_link}
            else:
                return {"success": False, "msg": f"Post failed with code {r.status_code}"}
        except Exception as e:
            logger.error(f"Post Error: {e}")
            return {"success": False}


    def _do_post_wp(self, data, status):
        # ... (Old WP logic) ...
        return {"success": False}

    def _save_local(self, data):
        # ... (Save as HTML locally) ...
        return {"success": False}
