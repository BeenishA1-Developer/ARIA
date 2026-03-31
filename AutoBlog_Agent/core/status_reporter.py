import os
import time
from datetime import datetime

class StatusReporter:
    _instance = None
    _logs = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StatusReporter, cls).__new__(cls)
        return cls._instance

    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": timestamp,
            "msg": message,
            "level": level
        }
        self._logs.append(entry)
        # Keep only last 100 logs
        if len(self._logs) > 100:
            self._logs.pop(0)

    def info(self, msg): self.log(msg, "info")
    def success(self, msg): self.log(msg, "success")
    def warning(self, msg): self.log(msg, "warning")
    def error(self, msg): self.log(msg, "error")

    def get_logs(self):
        return self._logs

reporter = StatusReporter()
