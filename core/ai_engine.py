# ============================================
# ARIA - core/ai_engine.py
# Google Gemini AI Integration
# ARIA ka asli dimaag
# ============================================

from loguru import logger
from rich.console import Console

console = Console()


class AIEngine:
    """
    ARIA ka AI brain — Google Gemini 1.5 Flash.
    Free, fast, aur powerful.
    Emails likhta hai, content banata hai, questions answer karta hai.
    """

    def __init__(self):
        self.model = None
        self.chat_history = []
        self._init_gemini()
        logger.info("✅ AI Engine (Gemini) initialized")

    def _init_gemini(self):
        """Gemini setup karo"""
        try:
            import google.generativeai as genai
            from config.settings import GEMINI_API_KEY, GEMINI_MODEL

            if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
                logger.warning("⚠️ GEMINI_API_KEY not set — AI features limited")
                return

            genai.configure(api_key=GEMINI_API_KEY)

            # ARIA ka system prompt
            system_prompt = """You are ARIA (Automated Responsive Intelligent Assistant), 
a helpful AI personal assistant. You help users with:
- Writing professional emails
- Organizing files and tasks
- Answering questions
- Providing smart recommendations

You respond in the same language as the user — if they write in Roman Urdu, reply in Roman Urdu.
If English, reply in English. Be concise, helpful, and professional.
When writing emails, always format them properly with subject and body."""

            self.model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=system_prompt
            )

            logger.info(f"✅ Gemini model ready: {GEMINI_MODEL}")

        except ImportError:
            logger.error("❌ google-generativeai not installed: pip install google-generativeai")
        except Exception as e:
            logger.error(f"❌ Gemini init error: {e}")

    def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        AI se response generate karo.
        Returns: Generated text ya error message
        """
        if not self.model:
            return self._offline_response(prompt)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                }
            )
            return response.text

        except Exception as e:
            logger.error(f"❌ Gemini generate error: {e}")
            return self._offline_response(prompt)

    def chat(self, user_message: str) -> str:
        """
        Conversation mode — history maintain karo.
        Better context samajhne ke liye.
        """
        if not self.model:
            return self._offline_response(user_message)

        try:
            # Simple conversation without persistent chat object issues
            # Build context from recent history
            context = ""
            if self.chat_history:
                recent = self.chat_history[-6:]  # Last 3 exchanges
                for item in recent:
                    context += f"User: {item['user']}\nARIA: {item['aria']}\n"

            full_prompt = f"{context}User: {user_message}\nARIA:"
            response_text = self.generate(full_prompt)

            # History mein save karo
            self.chat_history.append({
                "user": user_message,
                "aria": response_text
            })

            # History limit karo (memory save karne ke liye)
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            return response_text

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return "Mujhe abhi iska jawab nahi pata. Kuch aur poochein."

    def write_email(self, recipient: str, about: str, tone: str = "professional") -> dict:
        """AI se email likho — structured output"""
        prompt = f"""Write a professional email:
- To: {recipient}
- About: {about}  
- Tone: {tone}

Respond in this EXACT format:
SUBJECT: [subject line]
BODY:
[email body with proper greeting and sign-off]"""

        response = self.generate(prompt)
        return self._parse_email(response, recipient)

    def _parse_email(self, text: str, recipient: str) -> dict:
        """Email response parse karo"""
        subject = "Important Update"
        body = text

        for line in text.split('\n'):
            if line.startswith("SUBJECT:"):
                subject = line.replace("SUBJECT:", "").strip()
                body_start = text.find("BODY:")
                if body_start != -1:
                    body = text[body_start + 5:].strip()
                break

        return {"subject": subject, "body": body, "recipient": recipient}

    def answer_question(self, question: str) -> str:
        """General question ka jawab do"""
        return self.chat(question)

    def _offline_response(self, prompt: str) -> str:
        """Jab AI available na ho — basic responses"""
        prompt_lower = prompt.lower()
        if "email" in prompt_lower:
            return "SUBJECT: Following Up\nBODY:\nDear Sir/Madam,\n\nI hope this email finds you well.\n\nBest regards,\n[Your Name]"
        elif "hello" in prompt_lower or "hi" in prompt_lower:
            return "Hello! Main ARIA hun. Aapki kya madad kar sakta hun?"
        else:
            return "AI engine se connection nahi — GEMINI_API_KEY set karein .env mein."

    def clear_history(self):
        """Chat history clear karo"""
        self.chat_history = []
        logger.info("Chat history cleared")

    def is_ready(self) -> bool:
        """Check karo AI engine ready hai ya nahi"""
        return self.model is not None
