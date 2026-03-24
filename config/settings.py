# ============================================================
# ARIA - Configuration & Settings
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Create dirs if not exist
for d in [DATA_DIR, LOGS_DIR, OUTPUTS_DIR,
          OUTPUTS_DIR / "screenshots",
          OUTPUTS_DIR / "emails",
          OUTPUTS_DIR / "files"]:
    d.mkdir(parents=True, exist_ok=True)

# ============================================================
# API KEYS - .env file mein daalo
# ============================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", str(BASE_DIR / "config" / "gmail_credentials.json"))
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", str(DATA_DIR / "gmail_token.json"))

# ============================================================
# ARIA Personality Settings
# ============================================================
ARIA_NAME = "ARIA"
ARIA_LANGUAGE = "ur-en"  # Urdu + English mix
ARIA_VOICE_RATE = 150     # Words per minute
ARIA_VOICE_VOLUME = 0.9

# ============================================================
# NLP Settings
# ============================================================
CONFIDENCE_THRESHOLD = 0.6
MAX_CONTEXT_HISTORY = 10

# ============================================================
# Voice Settings
# ============================================================
WHISPER_MODEL = "base"    # base = fast, medium = accurate
SAMPLE_RATE = 16000
RECORD_SECONDS = 5
SILENCE_THRESHOLD = 0.01

# ============================================================
# Memory Settings
# ============================================================
DB_PATH = str(DATA_DIR / "aria_memory.db")
CHROMA_PATH = str(DATA_DIR / "chroma_db")
MAX_MEMORY_ITEMS = 1000

# ============================================================
# File Manager Settings
# ============================================================
SEARCH_PATHS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Pictures",
    Path.home() / "Videos",
]
MAX_FILE_RESULTS = 20

# ============================================================
# Email Settings
# ============================================================
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/contacts.readonly'
]

# ============================================================
# Gemini AI Settings
# ============================================================
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_MAX_TOKENS = 2048
GEMINI_TEMPERATURE = 0.7
