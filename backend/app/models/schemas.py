from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class AppState(str, Enum):
    IDLE = "IDLE"
    READY = "READY"
    REVIEWING = "REVIEWING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_USER_ACTION = "NEEDS_USER_ACTION"

class ResultStatus(str, Enum):
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    NEEDS_USER_ACTION = "NEEDS_USER_ACTION"
    UNKNOWN = "UNKNOWN"

class ContactTarget(BaseModel):
    id: str
    username: str
    display_name: Optional[str] = ""
    status: str = "active"
    last_active_days: Optional[int] = None
    last_active_provenance: str = "Unknown"
    notes: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ContactCreate(BaseModel):
    username: str
    display_name: Optional[str] = ""
    notes: Optional[str] = ""

class AuditLogEntry(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    workflow: str
    result: ResultStatus
    reason_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class DeviceInfo(BaseModel):
    device_id: str
    model: str = "Android Device"
    android_version: Optional[str] = "Unknown"
    snapchat_version: Optional[str] = "14.29.0.50"
    accessibility_enabled: bool = False
    overlay_enabled: bool = False
    notification_enabled: bool = False
    is_connected: bool = True
    last_heartbeat: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WorkflowActionRequest(BaseModel):
    action: str  # e.g., "demo_run", "friend_review", "streak_reminder"
    target_ids: List[str] = []
    parameters: Optional[Dict[str, Any]] = None

class WebSocketMessage(BaseModel):
    type: str
    payload: Any
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
