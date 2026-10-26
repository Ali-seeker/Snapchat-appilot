import json
import uuid
import re
from typing import List, Optional, Tuple
from pathlib import Path
from ..config import CONTACTS_FILE
from ..models.schemas import ContactTarget, ContactCreate

class ContactService:
    def __init__(self, file_path: Path = CONTACTS_FILE):
        self.file_path = file_path
        self._contacts: List[ContactTarget] = []
        self._load()
        if not self._contacts:
            self._seed_demo_contacts()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._contacts = [ContactTarget(**item) for item in data]
            except Exception:
                self._contacts = []

    def _save(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self._contacts], f, indent=2)
        except Exception:
            pass

    def _normalize_username(self, username: str) -> str:
        # Lowercase and remove excessive inner/outer whitespace
        cleaned = username.strip().lower()
        cleaned = re.sub(r"\s+", "", cleaned)
        return cleaned

    def validate_contact(self, username: str) -> Tuple[bool, str]:
        norm = self._normalize_username(username)
        if not norm:
            return False, "Username cannot be empty or whitespace only"
        if len(norm) < 3:
            return False, "Username must be at least 3 characters"
        if len(norm) > 30:
            return False, "Username cannot exceed 30 characters"
        if not re.match(r"^[a-z0-9._-]+$", norm):
            return False, "Username can only contain alphanumeric characters, dots, underscores, and dashes"
        return True, ""

    def add_contact(self, contact_in: ContactCreate) -> Tuple[Optional[ContactTarget], str]:
        is_valid, err = self.validate_contact(contact_in.username)
        if not is_valid:
            return None, err

        norm = self._normalize_username(contact_in.username)
        # Check duplicate
        for existing in self._contacts:
            if self._normalize_username(existing.username) == norm:
                return None, f"Target '{norm}' already exists in list (duplicate rejected)"

        new_contact = ContactTarget(
            id=str(uuid.uuid4())[:8],
            username=norm,
            display_name=contact_in.display_name.strip() if contact_in.display_name else norm,
            notes=contact_in.notes or "",
            last_active_days=None,
            last_active_provenance="Synthetic / Local Curated"
        )
        self._contacts.append(new_contact)
        self._save()
        return new_contact, ""

    def get_contacts(self) -> List[ContactTarget]:
        return self._contacts

    def get_contact_by_id(self, contact_id: str) -> Optional[ContactTarget]:
        for c in self._contacts:
            if c.id == contact_id:
                return c
        return None

    def remove_contact(self, contact_id: str) -> bool:
        initial_len = len(self._contacts)
        self._contacts = [c for c in self._contacts if c.id != contact_id]
        if len(self._contacts) != initial_len:
            self._save()
            return True
        return False

    def clear_contacts(self):
        self._contacts = []
        self._save()

    def _seed_demo_contacts(self):
        demo_list = [
            ContactCreate(username="alex.dev", display_name="Alex (Lead Engineer)", notes="Testing active streaks"),
            ContactCreate(username="sam_snap99", display_name="Samir Khan", notes="Daily streak candidate"),
            ContactCreate(username="taylor_creative", display_name="Taylor Swift-like", notes="Demo inactive candidate"),
            ContactCreate(username="jordan_b", display_name="Jordan B", notes="Synthetic test user"),
        ]
        for item in demo_list:
            self.add_contact(item)

contact_service = ContactService()
