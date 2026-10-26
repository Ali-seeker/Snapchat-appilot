import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from ..config import AUDIT_LOG_FILE
from ..models.schemas import AuditLogEntry, ResultStatus

class AuditLogger:
    def __init__(self, log_path: Path = AUDIT_LOG_FILE):
        self.log_path = log_path
        self._logs: List[AuditLogEntry] = []
        self._load()

    def _load(self):
        if self.log_path.exists():
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._logs = [AuditLogEntry(**item) for item in data]
            except Exception:
                self._logs = []
        else:
            self._logs = []

    def _save(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self._logs], f, indent=2)
        except Exception:
            pass

    def log(
        self,
        workflow: str,
        result: ResultStatus,
        reason_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        # Sanitize details to ensure no sensitive tokens or passwords
        safe_details = {}
        if details:
            for k, v in details.items():
                if any(bad in k.lower() for bad in ["pass", "token", "auth", "secret", "cookie"]):
                    safe_details[k] = "[REDACTED]"
                else:
                    safe_details[k] = v

        entry = AuditLogEntry(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            workflow=workflow,
            result=result,
            reason_code=reason_code,
            message=message,
            details=safe_details
        )
        self._logs.insert(0, entry)  # latest first
        if len(self._logs) > 500:
            self._logs = self._logs[:500]
        self._save()
        return entry

    def get_logs(self, limit: int = 50) -> List[AuditLogEntry]:
        return self._logs[:limit]

    def clear(self):
        self._logs = []
        self._save()

audit_logger = AuditLogger()
