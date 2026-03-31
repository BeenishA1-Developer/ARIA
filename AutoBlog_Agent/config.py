# ============================================================
# Blogging Pro Agent - CONFIGURATION
# ============================================================
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Site Settings ---
# WordPress Website URL: "https://yourblog.com"
SITE_URL     = os.getenv("BLOG_URL", "")
SITE_API_USER = os.getenv("WP_USER", "")
SITE_API_PASS = os.getenv("WP_PASS", "") # App Password for WordPress

# --- AI Settings ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
MODEL_NAME     = "gemini-1.5-flash-latest"

# --- Content Preferences ---
CONTENT_LANG    = "English" # Change to "Urdu" or "Mix"
POSTING_HOUR    = 10 # 10 AM (Target time for posts)
KEYWORD_COUNT   = 10 # How many keywords to research for trends
MIN_WORDS       = 1000

# --- Paths ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR  = BASE_DIR / "outputs"

for d in [DATA_DIR, OUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)
