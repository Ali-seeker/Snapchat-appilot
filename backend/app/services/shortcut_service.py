import json
import uuid
from typing import List, Optional
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, timezone

from ..models.schemas import ShortcutItem, ShortcutCreate

class ShortcutService:
    def __init__(self, data_path: Optional[Path] = None):
        self.file_path = data_path or (Path(__file__).parent.parent.parent / "data" / "shortcuts.json")
        self._shortcuts: List[ShortcutItem] = []
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._shortcuts = [ShortcutItem(**item) for item in data]
            except Exception:
                self._shortcuts = []
        else:
            # Seed with user's phone shortcut (Call me hand 🤙)
            self._shortcuts = [
                ShortcutItem(
                    id=str(uuid.uuid4())[:8],
                    name="Friends & Streaks",
                    emoji="🤙",
                    created_at=datetime.now(timezone.utc).isoformat()
                )
            ]
            self._save()

    def _save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self._shortcuts], f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_all(self) -> List[ShortcutItem]:
        return self._shortcuts

    def create(self, item_in: ShortcutCreate) -> ShortcutItem:
        new_item = ShortcutItem(
            id=str(uuid.uuid4())[:8],
            name=item_in.name.strip(),
            emoji=item_in.emoji.strip(),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        self._shortcuts.append(new_item)
        self._save()
        return new_item

    def delete(self, shortcut_id: str) -> bool:
        initial = len(self._shortcuts)
        self._shortcuts = [s for s in self._shortcuts if s.id != shortcut_id]
        if len(self._shortcuts) < initial:
            self._save()
            return True
        return False

shortcut_service = ShortcutService()
