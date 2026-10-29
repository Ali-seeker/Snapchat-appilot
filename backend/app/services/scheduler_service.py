import asyncio
import json
import uuid
from datetime import datetime, date, time as dt_time, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .adb_service import adb_service
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from ..models.schemas import ResultStatus, AppState

# Engines for direct execution
from .snapscore_engine import snapscore_engine
from .auto_snap_engine import auto_snap_engine
from .bulk_follow_engine import bulk_follow_engine
from .bulk_unfollow_engine import bulk_unfollow_engine


class ScheduleItem(BaseModel):
    id: str
    title: str
    automation_type: str  # "snapscore" | "snap" | "follow" | "unfollow"
    params: Dict[str, Any] = Field(default_factory=dict)
    date: str  # "YYYY-MM-DD"
    start_time: str  # "HH:MM"
    end_time: Optional[str] = None  # "HH:MM" (optional execution window)
    repeat_interval_minutes: Optional[int] = None  # (e.g. repeat every 60 mins within window)
    frequency: str = "once"  # "once" | "daily" | "weekly"
    is_active: bool = True
    last_run_at: Optional[str] = None
    last_status: Optional[str] = "PENDING"  # "PENDING" | "RUNNING" | "COMPLETED" | "DEVICE_OFFLINE" | "FAILED" | "WINDOW_EXPIRED"
    last_error: Optional[str] = None
    created_at: str


class ScheduleCreate(BaseModel):
    title: str
    automation_type: str
    params: Dict[str, Any] = Field(default_factory=dict)
    date: str
    start_time: str
    end_time: Optional[str] = None
    repeat_interval_minutes: Optional[int] = None
    frequency: str = "once"


class SchedulerService:
    def __init__(self, data_path: Optional[Path] = None):
        self.file_path = data_path or (Path(__file__).parent.parent.parent / "data" / "schedules.json")
        self._schedules: List[ScheduleItem] = []
        self._is_checking = False
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._schedules = [ScheduleItem(**item) for item in data]
            except Exception:
                self._schedules = []
        else:
            # Seed with useful sample scheduled templates
            today_str = datetime.now().strftime("%Y-%m-%d")
            self._schedules = [
                ScheduleItem(
                    id=str(uuid.uuid4())[:8],
                    title="Daily Evening Snapscore Multiplier",
                    automation_type="snapscore",
                    params={"cycles": 3, "recipient_mode": "count", "max_recipients": 5},
                    date=today_str,
                    start_time="20:00",
                    end_time="21:30",
                    frequency="daily",
                    is_active=True,
                    last_status="PENDING",
                    created_at=datetime.now().isoformat()
                ),
                ScheduleItem(
                    id=str(uuid.uuid4())[:8],
                    title="Morning Streak Filter Snap Send",
                    automation_type="snap",
                    params={"random_filter": True, "recipient_mode": "count", "max_recipients": 5},
                    date=today_str,
                    start_time="09:00",
                    frequency="daily",
                    is_active=True,
                    last_status="PENDING",
                    created_at=datetime.now().isoformat()
                )
            ]
            self._save()

    def _save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self._schedules], f, indent=2)
        except Exception:
            pass

    def get_all(self) -> List[ScheduleItem]:
        return self._schedules

    def get_by_id(self, schedule_id: str) -> Optional[ScheduleItem]:
        for s in self._schedules:
            if s.id == schedule_id:
                return s
        return None

    def create(self, item_in: ScheduleCreate) -> ScheduleItem:
        new_item = ScheduleItem(
            id=str(uuid.uuid4())[:8],
            title=item_in.title.strip() or f"Scheduled {item_in.automation_type.title()}",
            automation_type=item_in.automation_type,
            params=item_in.params,
            date=item_in.date,
            start_time=item_in.start_time,
            end_time=item_in.end_time,
            repeat_interval_minutes=item_in.repeat_interval_minutes,
            frequency=item_in.frequency,
            is_active=True,
            last_status="PENDING",
            created_at=datetime.now().isoformat()
        )
        self._schedules.append(new_item)
        self._save()
        return new_item

    def update(self, schedule_id: str, updates: Dict[str, Any]) -> Optional[ScheduleItem]:
        for s in self._schedules:
            if s.id == schedule_id:
                for k, v in updates.items():
                    if hasattr(s, k):
                        setattr(s, k, v)
                self._save()
                return s
        return None

    def delete(self, schedule_id: str) -> bool:
        before = len(self._schedules)
        self._schedules = [s for s in self._schedules if s.id != schedule_id]
        if len(self._schedules) < before:
            self._save()
            return True
        return False

    def toggle(self, schedule_id: str) -> Optional[ScheduleItem]:
        for s in self._schedules:
            if s.id == schedule_id:
                s.is_active = not s.is_active
                if s.is_active and s.last_status in ["DEVICE_OFFLINE", "FAILED"]:
                    s.last_status = "PENDING"
                    s.last_error = None
                self._save()
                return s
        return None

    async def execute_schedule(self, schedule: ScheduleItem, is_manual_trigger: bool = False) -> Dict[str, Any]:
        """
        Executes a scheduled automation with comprehensive pre-flight verification:
        1. Connectivity Check: Verifies mobile phone is plugged in via ADB.
        2. Concurrency Check: Checks if StateMachine is idle; defers if busy.
        3. Executes corresponding engine with saved parameters.
        4. Logs audit entry and records status.
        """
        now_str = datetime.now().isoformat()

        # Step 1: Pre-flight check - Is a mobile phone connected?
        devices = adb_service.list_devices()
        connected_devs = [d for d in devices if getattr(d, 'is_connected', True)]
        if not devices or (len(connected_devs) == 0 and not any(d.device_id for d in devices)):
            error_msg = f"Phone offline: Target device is not connected via ADB at scheduled time ({schedule.start_time})."
            schedule.last_status = "DEVICE_OFFLINE"
            schedule.last_error = error_msg
            schedule.last_run_at = now_str
            self._save()

            entry = audit_logger.log(
                workflow="Schedule Orchestrator",
                result=ResultStatus.FAILED,
                reason_code="SCHEDULE_DEVICE_OFFLINE",
                message=f"Scheduled run '{schedule.title}' aborted: Mobile phone is disconnected.",
                details={
                    "schedule_id": schedule.id,
                    "automation": schedule.automation_type,
                    "scheduled_time": f"{schedule.date} {schedule.start_time}",
                    "resolution": "Reconnect phone via USB and enable USB Debugging to resume automation."
                }
            )
            await ws_hub.broadcast_audit_log(entry)
            return {"status": "error", "reason": "DEVICE_OFFLINE", "message": error_msg}

        target_device_id = devices[0].device_id

        # Step 2: Concurrency & State Machine Guard
        if state_machine.is_running:
            defer_msg = f"System busy: Automation '{state_machine._current_workflow}' is actively running. Deferring scheduled run."
            schedule.last_error = defer_msg
            self._save()
            return {"status": "deferred", "reason": "SYSTEM_BUSY", "message": defer_msg}

        if state_machine.is_stopped:
            halt_msg = "Safety lock: System is currently under Emergency STOP. Skipping scheduled run."
            schedule.last_status = "STOPPED_SAFETY"
            schedule.last_error = halt_msg
            self._save()
            return {"status": "error", "reason": "EMERGENCY_STOP", "message": halt_msg}

        # Step 3: Dispatch Target Engine
        schedule.last_status = "RUNNING"
        schedule.last_error = None
        schedule.last_run_at = now_str
        self._save()

        p = schedule.params or {}
        auto_type = schedule.automation_type.lower()
        success = False
        res_summary = {}

        try:
            entry = audit_logger.log(
                workflow="Schedule Orchestrator",
                result=ResultStatus.COMPLETED,
                reason_code="SCHEDULE_STARTED",
                message=f"Triggering scheduled automation: '{schedule.title}' ({schedule.automation_type.upper()})",
                details={"schedule_id": schedule.id, "params": p, "is_manual": is_manual_trigger}
            )
            await ws_hub.broadcast_audit_log(entry)

            if auto_type == "snapscore":
                res = await snapscore_engine.run_booster_workflow(
                    device_id=target_device_id,
                    cycles=int(p.get("cycles", 3)),
                    select_all=bool(p.get("select_all", False)),
                    max_recipients=int(p.get("max_recipients", 5)),
                    recipient_mode=str(p.get("recipient_mode", "count")),
                    shortcut_emoji=p.get("shortcut_emoji"),
                    cooldown_seconds=int(p.get("cooldown_seconds", 15))
                )
                success = (res.get("status") == "ok")
                res_summary = res

            elif auto_type == "snap":
                res = await auto_snap_engine.run_snap_workflow(
                    device_id=target_device_id,
                    random_filter=bool(p.get("random_filter", True)),
                    select_all=bool(p.get("select_all", False)),
                    max_recipients=int(p.get("max_recipients", 5)),
                    recipient_mode=str(p.get("recipient_mode", "count")),
                    shortcut_emoji=p.get("shortcut_emoji")
                )
                success = (res.get("status") == "ok")
                res_summary = res

            elif auto_type == "follow":
                mode = p.get("mode", "quick_add")
                target_ids = p.get("target_ids", [])
                max_c = int(p.get("max_count", 5))
                res = await bulk_follow_engine.run_follow_workflow(
                    device_id=target_device_id,
                    mode=mode,
                    target_ids=target_ids,
                    max_count=max_c
                )
                success = (res.get("status") == "ok")
                res_summary = res

            elif auto_type == "unfollow":
                f_type = p.get("filter_type", "no_streak")
                days_th = int(p.get("days_threshold", 14))
                max_u = int(p.get("max_unfollow", 5))
                sel_all = bool(p.get("select_all", False))
                res = await bulk_unfollow_engine.run_unfollow_workflow(
                    device_id=target_device_id,
                    filter_type=f_type,
                    days_threshold=days_th,
                    max_unfollow=max_u,
                    select_all=sel_all
                )
                success = (res.get("status") == "ok")
                res_summary = res

            else:
                schedule.last_status = "FAILED"
                schedule.last_error = f"Unsupported automation type '{auto_type}'"
                self._save()
                return {"status": "error", "message": schedule.last_error}

            schedule.last_status = "COMPLETED" if success else "FAILED"
            schedule.last_error = None if success else "Workflow returned non-ok status"

            # Step 4: Advance recurring frequency or deactivate if run-once
            if schedule.frequency == "daily":
                # Advance date to tomorrow
                try:
                    curr_d = datetime.strptime(schedule.date, "%Y-%m-%d").date()
                    next_d = curr_d + timedelta(days=1)
                    schedule.date = next_d.strftime("%Y-%m-%d")
                    schedule.last_status = "PENDING"
                except Exception:
                    pass
            elif schedule.frequency == "once":
                schedule.is_active = False

            self._save()
            return {"status": "ok", "schedule_id": schedule.id, "result": res_summary}

        except Exception as e:
            schedule.last_status = "FAILED"
            schedule.last_error = str(e)
            self._save()
            audit_logger.log(
                workflow="Schedule Orchestrator",
                result=ResultStatus.FAILED,
                reason_code="SCHEDULE_EXECUTION_ERROR",
                message=f"Execution failed for schedule '{schedule.title}': {e}",
                details={"error": str(e)}
            )
            return {"status": "error", "message": str(e)}

    async def check_due_schedules(self):
        """Checks for pending schedules that are due for execution"""
        if self._is_checking:
            return
        self._is_checking = True

        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            curr_time_str = now.strftime("%H:%M")

            for s in list(self._schedules):
                if not s.is_active:
                    continue

                # Check if schedule date matches today or is past due
                if s.date > today_str:
                    continue

                # Parse start time
                try:
                    sched_hour, sched_min = map(int, s.start_time.split(":"))
                    sched_dt = datetime.combine(datetime.strptime(s.date, "%Y-%m-%d").date(), dt_time(sched_hour, sched_min))
                except Exception:
                    continue

                # Check window end if specified
                if s.end_time:
                    try:
                        end_h, end_m = map(int, s.end_time.split(":"))
                        end_dt = datetime.combine(datetime.strptime(s.date, "%Y-%m-%d").date(), dt_time(end_h, end_m))
                        if now > end_dt:
                            # Window has passed for today
                            if s.frequency == "daily":
                                curr_d = datetime.strptime(s.date, "%Y-%m-%d").date()
                                s.date = (curr_d + timedelta(days=1)).strftime("%Y-%m-%d")
                                s.last_status = "PENDING"
                            else:
                                s.is_active = False
                                s.last_status = "WINDOW_EXPIRED"
                            self._save()
                            continue
                    except Exception:
                        pass

                # If scheduled time has arrived or passed within the last 30 minutes
                time_diff = (now - sched_dt).total_seconds()
                if 0 <= time_diff <= 1800:
                    # Check if already ran today at this start_time
                    if s.last_run_at:
                        try:
                            last_run_dt = datetime.fromisoformat(s.last_run_at)
                            if (now - last_run_dt).total_seconds() < 300:
                                # Ran within last 5 minutes, prevent duplicate trigger
                                continue
                        except Exception:
                            pass

                    # Execute the due schedule
                    await self.execute_schedule(s)

        except Exception as e:
            pass
        finally:
            self._is_checking = False

    async def start_daemon(self, interval_seconds: int = 15):
        """Background loop monitoring scheduled runs"""
        while True:
            try:
                await self.check_due_schedules()
            except Exception:
                pass
            await asyncio.sleep(interval_seconds)


scheduler_service = SchedulerService()

