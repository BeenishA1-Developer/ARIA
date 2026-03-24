# 🤖 ARIA v2 — Automated Responsive Intelligent Assistant
### Phase 1 ✅ + Phase 2 ✅ — EK COMPLETE FILE MEIN

> Aapka 24/7 AI Personal Employee — Urdu + English + Roman Urdu

---

## 📁 Project Structure

```
ARIA/
├── main.py                        ← START YAHAN SE (Phase 1+2)
├── requirements.txt               ← All dependencies
├── setup.bat                      ← Windows one-click setup
├── run.bat                        ← ARIA start
├── run_tests.bat                  ← Tests chalao
├── .env.example                   ← API keys template
│
├── core/                          ← PHASE 1 — Core
│   ├── nlp_engine.py              ← Intent detection (50+ intents)
│   ├── voice_system.py            ← Whisper + pyttsx3
│   ├── memory_system.py           ← SQLite database
│   ├── task_planner.py            ← Step planner
│   ├── master_executor.py         ← Phase 1 brain
│   └── master_executor_v2.py      ← Phase 1+2 COMBINED brain ⭐
│
├── modules/                       ← PHASE 1 — Modules
│   ├── file_manager.py            ← Files search/organize/merge
│   ├── app_controller.py          ← Apps + screenshot + system
│   └── email_system.py            ← Email draft (Phase 1)
│
├── modules/phase2/                ← PHASE 2 — New Modules ⭐
│   ├── whatsapp_module.py         ← WhatsApp send (Twilio)
│   ├── gmail_full.py              ← Gmail send/read/reply/search
│   ├── fiverr_engine.py           ← Keywords/Competitor/Report
│   ├── task_scheduler.py          ← Background task scheduler
│   └── file_sender.py             ← File auto-send
│
├── config/
│   └── settings.py
│
├── tests/
│   ├── test_phase1.py             ← 46+ Phase 1 tests
│   └── test_phase2.py             ← 37+ Phase 2 tests
│
└── data/                          ← Auto-created
    ├── aria_memory.db
    └── scheduled_tasks.json
```

---

## 🚀 Setup (Windows — 5 Minutes)

### Step 1: Setup chalao
```
setup.bat  ← double click
```

### Step 2: .env file mein keys daalo
```
GEMINI_API_KEY=xxxx          ← FREE: aistudio.google.com
TWILIO_ACCOUNT_SID=xxxx      ← FREE trial: twilio.com
TWILIO_AUTH_TOKEN=xxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### Step 3: ARIA start karo
```
run.bat  ← double click
```

---

## 💬 Commands — Phase 1 ✅

| Command | Action |
|---------|--------|
| `hello aria` | Greeting |
| `screenshot lo` | Screen capture |
| `meri pdf files dhoondo` | PDF search |
| `chrome kholo` | App open |
| `system status batao` | CPU/RAM/Battery |
| `ahmed ko email likho` | AI email draft |
| `Downloads organize karo` | Files sort |
| `duplicate files dhoondo` | Duplicates |

## 💬 Commands — Phase 2 ✅

| Command | Action |
|---------|--------|
| `03001234567 ko message bhejo` | WhatsApp send |
| `inbox check karo` | Gmail inbox |
| `email bhejo` | Gmail send |
| `cv.pdf ahmed ko email bhejo` | File send |
| `logo design ke keywords do` | Fiverr keywords |
| `fiverr competitor analyze karo` | Competitor analysis |
| `fiverr report banao` | Performance report |
| `kal 9 baje email schedule karo` | Task scheduler |

---

## 🔑 API Keys (Sab FREE)

| Service | Link | Cost |
|---------|------|------|
| Gemini AI | aistudio.google.com | FREE |
| Gmail API | console.cloud.google.com | FREE |
| Twilio WhatsApp | twilio.com | FREE trial |

---

## 📋 Roadmap

| Phase | Status | Features |
|-------|--------|---------|
| **Phase 1** | ✅ COMPLETE | NLP, Voice, Memory, Files, Email Draft |
| **Phase 2** | ✅ COMPLETE | WhatsApp, Gmail Full, Fiverr, Scheduler |
| Phase 3 | 📋 Planned | Job Apply, TikTok, Website Generator |

---

*Built with ❤️ — Python + Google Gemini + OpenAI Whisper + Twilio*
