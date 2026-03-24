# ============================================================
# ARIA - Voice System v2
# Whisper (listen) + pyttsx3 (speak) — graceful fallbacks
# ============================================================

import os
import sys
import threading
import time
from loguru import logger

# --- Optional imports with graceful fallback ---
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper not installed — voice input disabled")

try:
    import sounddevice as sd
    import numpy as np
    # Test if PortAudio is actually usable
    sd.query_devices()
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False
    logger.warning("sounddevice/PortAudio not available — text input mode")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("pyttsx3 not installed — silent mode")


class VoiceSystem:
    """
    ARIA Voice System v2.
    - Whisper: voice input (offline, free)
    - pyttsx3: voice output (offline, free)  
    - Graceful fallback to text mode if hardware unavailable
    """

    def __init__(self, config: dict = None):
        config = config or {}
        self.sample_rate    = config.get("SAMPLE_RATE",     16000)
        self.record_seconds = config.get("RECORD_SECONDS",  5)
        self.voice_rate     = config.get("ARIA_VOICE_RATE",  150)
        self.voice_volume   = config.get("ARIA_VOICE_VOLUME", 0.9)
        self.whisper_model  = config.get("WHISPER_MODEL",   "base")

        self._tts_engine    = None
        self._whisper_model = None
        self._text_mode     = not SOUND_AVAILABLE

        self._init_tts()
        mode = "text" if self._text_mode else "voice"
        logger.info(f"Voice System v2 ready — mode={mode}")

    # ── TTS ───────────────────────────────────────────────────

    def _init_tts(self):
        """pyttsx3 initialize karo."""
        if not TTS_AVAILABLE:
            return
        try:
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty('rate',   self.voice_rate)
            self._tts_engine.setProperty('volume', self.voice_volume)
            voices = self._tts_engine.getProperty('voices')
            if voices:
                # Try to pick a female voice (usually index 1 on Windows)
                voice_idx = 1 if len(voices) > 1 else 0
                self._tts_engine.setProperty('voice', voices[voice_idx].id)
            logger.success("TTS engine ready (Female Voice)")
        except Exception as e:
            logger.warning(f"TTS init failed: {e} — silent mode")
            self._tts_engine = None

    def speak(self, text: str, blocking: bool = True):
        """ARIA bolti hai."""
        # Always print to console
        print(f"\n🤖 ARIA: {text}\n")

        if not self._tts_engine:
            return

        try:
            if blocking:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            else:
                t = threading.Thread(
                    target=self._speak_bg, args=(text,), daemon=True
                )
                t.start()
        except Exception as e:
            logger.warning(f"speak error: {e}")

    def _speak_bg(self, text: str):
        try:
            eng = pyttsx3.init()
            eng.setProperty('rate',   self.voice_rate)
            eng.setProperty('volume', self.voice_volume)
            eng.say(text)
            eng.runAndWait()
        except Exception as e:
            logger.debug(f"bg speak error: {e}")

    # ── LISTEN ────────────────────────────────────────────────

    def _load_whisper(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None and WHISPER_AVAILABLE:
            logger.info("Loading Whisper model (first time)...")
            self._whisper_model = whisper.load_model(self.whisper_model)
            logger.success(f"Whisper '{self.whisper_model}' loaded!")
        return self._whisper_model

    def listen(self) -> str:
        """
        Microphone se suno — ya text input lo.
        Auto-detects available mode.
        """
        if self._text_mode or not SOUND_AVAILABLE:
            return self._text_input()

        model = self._load_whisper()
        if not model:
            return self._text_input()

        try:
            print(f"\n🎤 Bol rahe ho... ({self.record_seconds}s)\n")
            audio = sd.rec(
                int(self.record_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            result = model.transcribe(
                audio.flatten(),
                language=None,
                task="transcribe"
            )
            text = result["text"].strip()
            if text:
                print(f"\n👤 Aap ne kaha: {text}\n")
                logger.info(f"Transcribed: {text}")
            return text
        except Exception as e:
            logger.error(f"listen error: {e}")
            return self._text_input()

    def _text_input(self) -> str:
        """Keyboard se input lo."""
        try:
            return input("\n💬 Command: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "stop"

    # ── SETTINGS ─────────────────────────────────────────────

    def set_voice_rate(self, rate: int):
        self.voice_rate = rate
        if self._tts_engine:
            self._tts_engine.setProperty('rate', rate)

    def set_voice_volume(self, volume: float):
        self.voice_volume = max(0.0, min(1.0, volume))
        if self._tts_engine:
            self._tts_engine.setProperty('volume', self.voice_volume)

    @property
    def is_voice_mode(self) -> bool:
        return not self._text_mode and SOUND_AVAILABLE

    @property 
    def is_tts_available(self) -> bool:
        return self._tts_engine is not None
