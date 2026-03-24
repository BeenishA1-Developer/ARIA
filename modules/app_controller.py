# ============================================================
# ARIA — App Controller v3 (Windows-safe imports)
# ============================================================

import os
import subprocess
import platform
import threading
import time
from pathlib import Path
from datetime import datetime
from loguru import logger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# pyautogui — only import when actually needed (Windows needs display)
PYAUTOGUI_AVAILABLE = False
_pyautogui = None

def _get_pyautogui():
    global PYAUTOGUI_AVAILABLE, _pyautogui
    if _pyautogui is not None:
        return _pyautogui
    try:
        import pyautogui
        _pyautogui = pyautogui
        PYAUTOGUI_AVAILABLE = True
        return _pyautogui
    except Exception:
        return None


class AppController:
    """
    ✅ Apps open/close
    ✅ System status (CPU/RAM/Battery/Disk)
    ✅ Screenshot (with lazy pyautogui import)
    ✅ Scheduled screenshots — background thread
    ✅ Volume control
    ✅ Full diagnostics
    ✅ Open URL
    """

    APP_MAP = {
        "chrome":        ["chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
        "firefox":       ["firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"],
        "notepad":       ["notepad", "notepad.exe"],
        "notepad++":     ["notepad++", r"C:\Program Files\Notepad++\notepad++.exe"],
        "calculator":    ["calc", "calculator"],
        "excel":         ["excel", r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"],
        "word":          ["winword", r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"],
        "powerpoint":    ["powerpnt"],
        "vlc":           ["vlc", r"C:\Program Files\VideoLAN\VLC\vlc.exe"],
        "spotify":       ["spotify", str(Path.home() / "AppData/Roaming/Spotify/Spotify.exe")],
        "vscode":        ["code"],
        "explorer":      ["explorer"],
        "task manager":  ["taskmgr"],
        "paint":         ["mspaint"],
        "cmd":           ["cmd"],
        "powershell":    ["powershell"],
        "settings":      ["ms-settings:"],
        "snipping tool": ["snippingtool"],
    }

    def __init__(self):
        self.system = platform.system()
        self._screenshot_thread  = None
        self._screenshot_running = False
        logger.info(f"App Controller v3 — {self.system}")

    # ── OPEN APP ──────────────────────────────────────────────

    def open_app(self, app_name: str) -> dict:
        key = app_name.lower().strip()
        for k, cmds in self.APP_MAP.items():
            if key in k or key == k:
                return self._launch(k, cmds)
        for k in self.APP_MAP:
            if key in k:
                return self._launch(k, self.APP_MAP[k])
        return self._launch_direct(app_name)

    def _launch(self, name: str, cmds: list) -> dict:
        for cmd in cmds:
            try:
                if isinstance(cmd, str) and cmd.startswith("ms-"):
                    os.startfile(cmd)
                elif Path(str(cmd)).exists():
                    subprocess.Popen([cmd])
                else:
                    subprocess.Popen(cmd, shell=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                logger.success(f"App opened: {name}")
                return {"success": True, "app": name,
                        "message": f"{name.capitalize()} khul gaya!"}
            except Exception:
                continue
        return {"success": False, "app": name,
                "message": f"{name} nahi khul saka"}

    def _launch_direct(self, name: str) -> dict:
        try:
            subprocess.Popen(name, shell=True,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return {"success": True, "app": name,
                    "message": f"{name} launch kiya!"}
        except Exception as e:
            return {"success": False, "app": name,
                    "message": f"{name} nahi mila: {e}"}

    # ── CLOSE APP ─────────────────────────────────────────────

    def close_app(self, app_name: str) -> dict:
        if not PSUTIL_AVAILABLE:
            return {"success": False, "message": "psutil nahi hai"}
        app_lower = app_name.lower()
        proc_map  = {
            "chrome":     ["chrome.exe"],
            "firefox":    ["firefox.exe"],
            "notepad":    ["notepad.exe"],
            "excel":      ["EXCEL.EXE", "excel.exe"],
            "word":       ["WINWORD.EXE", "winword.exe"],
            "vlc":        ["vlc.exe"],
            "spotify":    ["Spotify.exe"],
            "vscode":     ["Code.exe"],
        }
        targets = next(
            (v for k, v in proc_map.items() if app_lower in k),
            [f"{app_lower}.exe"]
        )
        killed = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if any(proc.info['name'].lower() == t.lower()
                       for t in targets):
                    proc.kill()
                    killed.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed:
            return {"success": True,
                    "message": f"{app_name.capitalize()} band ho gaya!"}
        return {"success": False,
                "message": f"{app_name} chal nahi raha tha"}

    # ── SYSTEM STATUS ─────────────────────────────────────────

    def get_system_status(self) -> dict:
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil install karo: pip install psutil"}
        try:
            cpu   = psutil.cpu_percent(interval=0.5)
            ram   = psutil.virtual_memory()
            disk_p = 'C:\\' if self.system == 'Windows' else '/'
            disk  = psutil.disk_usage(disk_p)
            bat   = psutil.sensors_battery()
            return {
                "cpu": {
                    "usage":  f"{cpu}%",
                    "cores":  psutil.cpu_count(logical=True),
                    "status": "High" if cpu > 80 else "Normal",
                },
                "ram": {
                    "total":   f"{ram.total/1024**3:.1f} GB",
                    "used":    f"{ram.used/1024**3:.1f} GB",
                    "percent": f"{ram.percent}%",
                    "status":  "High" if ram.percent > 80 else "Normal",
                },
                "disk": {
                    "total":   f"{disk.total/1024**3:.1f} GB",
                    "used":    f"{disk.used/1024**3:.1f} GB",
                    "free":    f"{disk.free/1024**3:.1f} GB",
                    "percent": f"{disk.percent}%",
                    "status":  "Low Space" if disk.percent > 85 else "Normal",
                },
                "battery": {
                    "percent": round(bat.percent, 1),
                    "plugged": bat.power_plugged,
                    "status":  "Charging" if bat.power_plugged else "Discharging",
                } if bat else None,
                "processes": len(list(psutil.process_iter())),
            }
        except Exception as e:
            logger.error(f"System status error: {e}")
            return {"error": str(e)}

    # ── SCREENSHOT ────────────────────────────────────────────

    def take_screenshot(self, save_path: str = None) -> str:
        """Screenshot — uses Pillow fallback if pyautogui unavailable."""
        if not save_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = str(
                Path("outputs/screenshots") / f"screenshot_{ts}.png"
            )
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)

        pag = _get_pyautogui()
        if pag:
            try:
                pag.screenshot().save(save_path)
                logger.success(f"Screenshot: {save_path}")
                return save_path
            except Exception as e:
                logger.warning(f"pyautogui screenshot failed: {e}")

        # Fallback — Pillow ImageGrab (Windows) or solid image
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(save_path)
            logger.success(f"Screenshot (ImageGrab): {save_path}")
            return save_path
        except Exception:
            pass

        # Final fallback — create placeholder image
        try:
            from PIL import Image, ImageDraw
            img  = Image.new('RGB', (800, 600), color=(30, 30, 30))
            draw = ImageDraw.Draw(img)
            draw.text((300, 280), "ARIA Screenshot", fill=(0, 200, 100))
            draw.text((250, 320),
                      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                      fill=(150, 150, 150))
            img.save(save_path)
            logger.info(f"Screenshot placeholder: {save_path}")
            return save_path
        except Exception as e:
            return f"Error: {e}"

    # ── SCHEDULED SCREENSHOTS ─────────────────────────────────

    def start_scheduled_screenshots(self, interval_minutes: int = 30,
                                     save_folder: str = None) -> dict:
        """Har N minutes mein automatically screenshot lo."""
        if self._screenshot_running:
            return {"success": False,
                    "message": "Already chal rahe hain"}

        folder = Path(save_folder or "outputs/screenshots/scheduled")
        folder.mkdir(parents=True, exist_ok=True)
        self._screenshot_running = True
        interval_sec = interval_minutes * 60

        def _loop():
            logger.info(f"Scheduled screenshots: every {interval_minutes}m")
            while self._screenshot_running:
                ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = str(folder / f"scheduled_{ts}.png")
                self.take_screenshot(path)
                time.sleep(interval_sec)

        self._screenshot_thread = threading.Thread(
            target=_loop, daemon=True
        )
        self._screenshot_thread.start()
        return {
            "success":  True,
            "interval": interval_minutes,
            "folder":   str(folder),
            "message":  f"Har {interval_minutes} minute mein screenshot lega!",
        }

    def stop_scheduled_screenshots(self) -> dict:
        self._screenshot_running = False
        return {"success": True,
                "message": "Scheduled screenshots band ho gayi"}

    # ── DIAGNOSTICS ───────────────────────────────────────────

    def run_diagnostics(self) -> dict:
        """Full ARIA system health check."""
        results = {}

        # System resources
        status = self.get_system_status()
        results["system"] = {
            "ok":      "error" not in status,
            "cpu":     status.get("cpu", {}).get("usage", "N/A"),
            "ram":     status.get("ram", {}).get("percent", "N/A"),
            "disk":    status.get("disk", {}).get("status", "N/A"),
            "battery": (str(status["battery"]["percent"]) + "%"
                        if status.get("battery") else "N/A"),
        }

        # Python packages
        packages = {
            "google.generativeai": "Gemini AI",
            "whisper":             "Voice Input",
            "pyttsx3":             "Voice Output",
            "sounddevice":         "Microphone",
            "psutil":              "System Monitor",
            "chromadb":            "Semantic Memory",
            "twilio":              "WhatsApp",
            "reportlab":           "PDF Reports",
            "schedule":            "Task Scheduler",
            "playwright":          "Web Automation (Phase 3)",
            "PIL":                 "Image Processing",
        }
        pkg_status = {}
        for pkg, name in packages.items():
            try:
                import importlib.util
                spec = importlib.util.find_spec(pkg.split(".")[0])
                if spec is not None:
                    pkg_status[name] = "✅ OK"
                else:
                    pkg_status[name] = "❌ Not installed"
            except Exception:
                pkg_status[name] = "❌ Not installed"
        results["packages"] = pkg_status

        # Config / API keys
        results["config"] = {
            "Gemini API Key":    "✅ Set" if os.getenv("GEMINI_API_KEY")         else "❌ Not set",
            "Gmail Credentials": "✅ Found" if Path("config/gmail_credentials.json").exists() else "❌ Not found",
            "Twilio SID":        "✅ Set" if os.getenv("TWILIO_ACCOUNT_SID")     else "❌ Not set",
            "Twilio Token":      "✅ Set" if os.getenv("TWILIO_AUTH_TOKEN")       else "❌ Not set",
        }

        # Folders
        results["folders"] = {
            d: "✅ OK" if Path(d).exists() else "❌ Missing"
            for d in ["data", "outputs", "outputs/screenshots",
                      "outputs/fiverr", "logs", "config"]
        }

        # Overall score
        issues = (
            [n for n, s in pkg_status.items() if "❌" in s] +
            [k for k, v in results["config"].items() if "❌" in v] +
            [k for k, v in results["folders"].items() if "❌" in v]
        )
        results["overall"] = {
            "status": "Healthy" if not issues else "Issues Found",
            "issues": issues,
            "score":  f"{max(0, 100 - len(issues) * 8)}/100",
        }
        logger.info(f"Diagnostics: {results['overall']['score']}")
        return results

    # ── VOLUME CONTROL ────────────────────────────────────────

    def control_volume(self, action: str, amount: int = 10) -> dict:
        pag = _get_pyautogui()
        if not pag:
            return {"success": False,
                    "message": "pyautogui not available (needs display)"}
        try:
            key_map = {"up": "volumeup", "down": "volumedown",
                       "mute": "volumemute", "unmute": "volumemute"}
            key = key_map.get(action)
            if key:
                presses = max(1, min(amount // 10, 10))
                for _ in range(presses):
                    pag.press(key)
            return {"success": True, "action": action,
                    "message": f"Volume {action} ho gaya!"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ── OPEN URL ──────────────────────────────────────────────

    def open_url(self, url: str) -> dict:
        """Browser mein koi bhi URL/website kholo."""
        try:
            import webbrowser
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return {"success": True, "url": url,
                    "message": f"Browser mein khul gaya: {url}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
