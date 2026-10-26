import json
import uuid
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime

class ReminderItem(BaseModel):
    id: str
    contact_id: str
    recipient_label: str
    reminder_time: str
    draft_text: str
    is_completed: bool = False
    created_at: str

class ReminderCreate(BaseModel):
    contact_id: str
    recipient_label: str
    reminder_time: str
    draft_text: str

class ReminderService:
    def __init__(self, data_path: Optional[Path] = None):
        self.file_path = data_path or (Path(__file__).parent.parent.parent / "data" / "reminders.json")
        self._reminders: List[ReminderItem] = []
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._reminders = [ReminderItem(**item) for item in data]
            except Exception:
                self._reminders = []
        else:
            self._reminders = [
                ReminderItem(
                    id=str(uuid.uuid4())[:8],
                    contact_id="1",
                    recipient_label="@testuser",
                    reminder_time="20:00 (Daily)",
                    draft_text="🔥 Daily Streak: Snap + Filter checklist",
                    is_completed=False,
                    created_at=datetime.utcnow().isoformat()
                )
            ]
            self._save()

    def _save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self._reminders], f, indent=2)
        except Exception:
            pass

    def get_all(self) -> List[ReminderItem]:
        return self._reminders

    def create(self, item_in: ReminderCreate) -> ReminderItem:
        new_item = ReminderItem(
            id=str(uuid.uuid4())[:8],
            contact_id=item_in.contact_id,
            recipient_label=item_in.recipient_label,
            reminder_time=item_in.reminder_time,
            draft_text=item_in.draft_text,
            is_completed=False,
            created_at=datetime.utcnow().isoformat()
        )
        self._reminders.append(new_item)
        self._save()
        return new_item

    def toggle(self, reminder_id: str) -> Optional[ReminderItem]:
        for r in self._reminders:
            if r.id == reminder_id:
                r.is_completed = not r.is_completed
                self._save()
                return r
        return None

    def delete(self, reminder_id: str) -> bool:
        initial = len(self._reminders)
        self._reminders = [r for r in self._reminders if r.id != reminder_id]
        if len(self._reminders) < initial:
            self._save()
            return True
        return False

reminder_service = ReminderService()
