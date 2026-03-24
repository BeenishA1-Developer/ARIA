# ============================================================
# ARIA - Task Planner
# Complex commands ko chhote steps mein todta hai
# ============================================================

from loguru import logger


class TaskPlanner:
    """
    ARIA ka Task Planner.
    Ek complex command ko steps mein todta hai.
    Phir ek ek step execute karta hai.
    """

    def __init__(self):
        # Intent → steps mapping
        self.task_flows = self._build_task_flows()
        logger.info("Task Planner initialized")

    def _build_task_flows(self) -> dict:
        """Har intent ke liye steps define karo."""
        return {
            "greeting": [
                {"action": "speak", "text": "Salam! Main ARIA hun — aapka AI assistant. Kya kar sakta hun aapke liye?"},
                {"action": "show_capabilities"},
            ],
            "screenshot": [
                {"action": "speak", "text": "Screenshot le raha hun..."},
                {"action": "take_screenshot"},
                {"action": "speak_result", "template": "Screenshot le liya! {path} mein save ho gaya."},
            ],
            "file_search": [
                {"action": "speak", "text": "Files dhoond raha hun — thak sa waqt lagega..."},
                {"action": "search_files"},
                {"action": "speak_result", "template": "{count} files mili hain!"},
                {"action": "show_file_results"},
            ],
            "file_organize": [
                {"action": "speak", "text": "Pehle dekh leta hun kitni files hain..."},
                {"action": "preview_organize"},
                {"action": "confirm", "message": "Kya main {count} files organize karun?"},
                {"action": "organize_files"},
                {"action": "speak_result", "template": "Ho gaya! {count} files organize ho gayi!"},
            ],
            "app_open": [
                {"action": "speak", "text": "Khol raha hun..."},
                {"action": "open_application"},
                {"action": "speak_result", "template": "{app} khul gaya!"},
            ],
            "app_close": [
                {"action": "speak", "text": "Band kar raha hun..."},
                {"action": "close_application"},
                {"action": "speak_result", "template": "{app} band ho gaya!"},
            ],
            "system_status": [
                {"action": "speak", "text": "System check kar raha hun..."},
                {"action": "get_system_status"},
                {"action": "speak_status"},
                {"action": "show_status"},
            ],
            "email_draft": [
                {"action": "speak", "text": "Email draft kar raha hun AI se..."},
                {"action": "draft_email"},
                {"action": "show_email_draft"},
                {"action": "confirm", "message": "Kya yeh email send karun?"},
            ],
            "email_send": [
                {"action": "confirm", "message": "Pakka email bhejun?"},
                {"action": "send_email"},
                {"action": "speak_result", "template": "Email bhej diya {recipient} ko!"},
            ],
            "find_duplicates": [
                {"action": "speak", "text": "Duplicate files dhoond raha hun..."},
                {"action": "find_duplicate_files"},
                {"action": "speak_result", "template": "{count} duplicate files mili hain!"},
                {"action": "show_duplicates"},
            ],
            "pdf_merge": [
                {"action": "speak", "text": "PDFs merge kar raha hun..."},
                {"action": "merge_pdf_files"},
                {"action": "speak_result", "template": "PDFs merge ho gayi! {path} pe save hain."},
            ],
            "file_create": [
                {"action": "create_file_or_folder"},
                {"action": "speak_result", "template": "{name} ban gaya!"},
            ],
            "volume_control": [
                {"action": "control_volume"},
                {"action": "speak_result", "template": "Volume {action} ho gaya!"},
            ],
            "time_date": [
                {"action": "get_time_date"},
                {"action": "speak_result", "template": "Abhi {time} baj rahe hain, {date} hai."},
            ],
            "help": [
                {"action": "show_help"},
                {"action": "speak", "text": "Yeh hain meri capabilities! Kya karna hai aapko?"},
            ],
            "stop": [
                {"action": "speak", "text": "Khuda hafiz! Main band ho raha hun. Allah hafiz!"},
                {"action": "shutdown"},
            ],
            "unknown": [
                {"action": "speak", "text": "Mujhe samajh nahi aaya. Kya aap thoda aur wazeh kar sakte hain?"},
                {"action": "ask_clarification"},
            ],
        }

    def plan(self, intent_result: dict) -> list:
        """
        Intent se execution plan banao.
        Returns: List of steps to execute
        """
        intent = intent_result.get("intent", "unknown")
        entities = intent_result.get("entities", {})

        steps = self.task_flows.get(intent, self.task_flows["unknown"])

        # Entities ko steps mein inject karo
        enriched_steps = []
        for step in steps:
            enriched = dict(step)
            enriched["entities"] = entities
            enriched["intent"] = intent
            enriched_steps.append(enriched)

        logger.info(f"Plan created: {intent} → {len(enriched_steps)} steps")
        return enriched_steps

    def requires_confirmation(self, intent: str) -> bool:
        """Kya yeh action confirm karna chahiye?"""
        # Risky actions — pehle poochna chahiye
        risky_intents = {
            "email_send",
            "file_organize",
            "find_duplicates",
            "pdf_merge",
            "app_close",
        }
        return intent in risky_intents
