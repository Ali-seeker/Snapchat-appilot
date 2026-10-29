import json
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models.schemas import (
    AppState, ResultStatus, ContactTarget, ContactCreate,
    AuditLogEntry, DeviceInfo, WorkflowActionRequest
)
from .services.state_machine import state_machine
from .services.audit_logger import audit_logger
from .services.contact_service import contact_service
from .services.adb_service import adb_service
from .services.websocket_hub import ws_hub
from .services.demo_engine import demo_engine
from .services.live_automation_engine import live_engine
from .services.reminder_service import reminder_service, ReminderItem, ReminderCreate
from .services.shortcut_service import shortcut_service, ShortcutItem, ShortcutCreate
from .services.bulk_follow_engine import bulk_follow_engine
from .services.bulk_unfollow_engine import bulk_unfollow_engine
from .services.auto_snap_engine import auto_snap_engine
from .services.snapscore_engine import snapscore_engine
from .services.chained_workflow_engine import chained_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register state machine listener to broadcast state changes
    async def state_listener(state: AppState, workflow: str | None):
        await ws_hub.broadcast_state(state, workflow)
    state_machine.register_listener(state_listener)

    # Initial log
    audit_logger.log(
        workflow="System",
        result=ResultStatus.COMPLETED,
        reason_code="SERVER_START",
        message="Appilot Backend Orchestrator started successfully"
    )

    # Background keep-alive to ensure ADB reverse tunnel stays alive persistently
    async def reverse_port_heartbeat():
        while True:
            try:
                if adb_service.is_adb_available():
                    devices = adb_service.list_devices()
                    for dev in devices:
                        adb_service.reverse_port(dev.device_id)
            except Exception:
                pass
            await asyncio.sleep(8)

    heartbeat_task = asyncio.create_task(reverse_port_heartbeat())
    try:
        yield
    finally:
        heartbeat_task.cancel()

app = FastAPI(title="Appilot Snapchat Companion API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- REST Endpoints ----------------- #

@app.get("/api/status")
async def get_system_status():
    adb_devs = adb_service.list_devices()
    ws_devs = ws_hub.get_all_devices()
    all_devs = {d.device_id: d for d in ws_devs}
    for d in adb_devs:
        if d.device_id not in all_devs:
            all_devs[d.device_id] = d
    snapchat_ver = "14.29.0.50"
    for d in all_devs.values():
        if getattr(d, "snapchat_version", None):
            snapchat_ver = d.snapchat_version
            break

    return {
        "state": state_machine.current_state.value,
        "workflow": state_machine.current_workflow,
        "is_paused": state_machine.is_paused,
        "is_stopped": state_machine.is_stopped,
        "adb_available": adb_service.is_adb_available(),
        "snapchat_version": snapchat_ver,
        "devices": list(all_devs.values())
    }

@app.get("/api/devices")
async def list_devices():
    adb_devs = adb_service.list_devices()
    ws_devs = ws_hub.get_all_devices()
    # Merge unique
    all_devs = {d.device_id: d for d in ws_devs}
    for d in adb_devs:
        if d.device_id not in all_devs:
            all_devs[d.device_id] = d
    return list(all_devs.values())

@app.post("/api/devices/reverse")
async def setup_adb_reverse(device_id: str):
    success = adb_service.reverse_port(device_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to run adb reverse")
    return {"status": "ok", "message": f"Port reverse established for device {device_id}"}

@app.get("/api/contacts", response_model=List[ContactTarget])
async def get_contacts():
    return contact_service.get_contacts()

@app.post("/api/contacts", response_model=ContactTarget)
async def create_contact(contact_in: ContactCreate):
    contact, err = contact_service.add_contact(contact_in)
    if not contact:
        raise HTTPException(status_code=400, detail=err)
    audit_logger.log(
        workflow="Contact Manager",
        result=ResultStatus.COMPLETED,
        reason_code="CONTACT_ADDED",
        message=f"Added contact @{contact.username}"
    )
    return contact

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    success = contact_service.remove_contact(contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contact not found")
    audit_logger.log(
        workflow="Contact Manager",
        result=ResultStatus.COMPLETED,
        reason_code="CONTACT_REMOVED",
        message=f"Removed contact ID {contact_id}"
    )
    return {"status": "ok"}

# ----------------- FR-07 & FR-08: Reminders & Drafts ----------------- #

@app.get("/api/reminders", response_model=List[ReminderItem])
async def get_reminders():
    return reminder_service.get_all()

@app.post("/api/reminders", response_model=ReminderItem)
async def create_reminder(item_in: ReminderCreate):
    created = reminder_service.create(item_in)
    audit_logger.log(
        workflow="Streak Reminder",
        result=ResultStatus.COMPLETED,
        reason_code="REMINDER_CREATED",
        message=f"Created streak reminder for {item_in.recipient_label} at {item_in.reminder_time}"
    )
    return created

@app.post("/api/reminders/{reminder_id}/toggle")
async def toggle_reminder(reminder_id: str):
    updated = reminder_service.toggle(reminder_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return updated

@app.delete("/api/reminders/{reminder_id}")
async def delete_reminder(reminder_id: str):
    success = reminder_service.delete(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "ok"}


@app.get("/api/shortcuts", response_model=List[ShortcutItem])
async def list_shortcuts():
    return shortcut_service.get_all()

@app.post("/api/shortcuts", response_model=ShortcutItem)
async def create_shortcut(item_in: ShortcutCreate):
    created = shortcut_service.create(item_in)
    audit_logger.log(
        workflow="Snap Shortcuts",
        result=ResultStatus.COMPLETED,
        reason_code="SHORTCUT_CREATED",
        message=f"Created shortcut '{item_in.name}' with emoji {item_in.emoji}"
    )
    return created

@app.delete("/api/shortcuts/{shortcut_id}")
async def delete_shortcut(shortcut_id: str):
    success = shortcut_service.delete(shortcut_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shortcut not found")
    return {"status": "ok"}

@app.post("/api/control/transition")
async def transition_state(state: AppState, workflow: str = "Manual"):
    try:
        state_machine.transition_to(state, workflow=workflow)
        return {"status": "ok", "state": state_machine.current_state.value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/control/pause")
async def pause_execution():
    ok = state_machine.request_pause()
    return {"status": "ok" if ok else "ignored", "state": state_machine.current_state.value}

@app.post("/api/control/resume")
async def resume_execution():
    ok = state_machine.request_resume()
    return {"status": "ok" if ok else "ignored", "state": state_machine.current_state.value}

@app.post("/api/control/stop")
async def stop_execution():
    state_machine.request_stop()
    await ws_hub.send_command_to_devices({"command": "STOP"})
    return {"status": "ok", "state": state_machine.current_state.value}

@app.post("/api/control/reset")
async def reset_execution():
    state_machine.reset_to_idle()
    return {"status": "ok", "state": state_machine.current_state.value}

class DemoRunRequest(BaseModel):
    scenario: str = "full_suite"
    target_ids: List[str] = []

@app.post("/api/demo/run")
async def run_demo(req: DemoRunRequest):
    asyncio.create_task(demo_engine.run_scenario(req.scenario, req.target_ids))
    return {"status": "started", "scenario": req.scenario}

class LiveRunRequest(BaseModel):
    device_id: Optional[str] = None
    target_ids: List[str] = []
    action: str = "add"

def _resolve_device_id(dev_id: Optional[str]) -> str:
    if dev_id:
        return dev_id
    devices = adb_service.list_devices()
    return devices[0].device_id if devices else "08265372BO000706"

@app.post("/api/live/run")
async def run_live_automation(req: LiveRunRequest):
    dev_id = _resolve_device_id(req.device_id)
    asyncio.create_task(live_engine.run_live_add_workflow(dev_id, req.target_ids))
    return {"status": "started", "device_id": dev_id, "targets_count": len(req.target_ids)}

# --- Day 3 Dedicated Production Endpoints --- #

class FollowWorkflowRequest(BaseModel):
    mode: str = "quick_add"  # "search" | "quick_add" | "accept"
    target_ids: Optional[List[str]] = []
    max_count: int = 10
    device_id: Optional[str] = None

@app.post("/api/workflow/follow")
async def start_follow_workflow(req: FollowWorkflowRequest):
    dev_id = _resolve_device_id(req.device_id)
    if not adb_service.list_devices():
        asyncio.create_task(demo_engine.run_demo_follow(req.mode, req.max_count, req.target_ids))
        return {"status": "started", "mode": req.mode, "device_id": "simulated"}

    asyncio.create_task(bulk_follow_engine.run_follow_workflow(
        device_id=dev_id,
        mode=req.mode,
        target_ids=req.target_ids,
        max_count=req.max_count
    ))
    return {"status": "started", "mode": req.mode, "device_id": dev_id}

class UnfollowWorkflowRequest(BaseModel):
    filter_type: str = "no_streak"  # "no_streak" | "inactive" | "custom"
    days_threshold: int = 14
    custom_targets: Optional[List[str]] = []
    max_unfollow: int = 10
    select_all: bool = False
    device_id: Optional[str] = None

@app.post("/api/workflow/unfollow")
async def start_unfollow_workflow(req: UnfollowWorkflowRequest):
    dev_id = _resolve_device_id(req.device_id)
    if not adb_service.list_devices():
        asyncio.create_task(demo_engine.run_demo_unfollow(req.filter_type, req.days_threshold, req.max_unfollow))
        return {"status": "started", "filter_type": req.filter_type, "device_id": "simulated"}

    asyncio.create_task(bulk_unfollow_engine.run_unfollow_workflow(
        device_id=dev_id,
        filter_type=req.filter_type,
        days_threshold=req.days_threshold,
        custom_targets=req.custom_targets,
        max_unfollow=req.max_unfollow,
        select_all=req.select_all
    ))
    return {"status": "started", "filter_type": req.filter_type, "device_id": dev_id}

class SnapWorkflowRequest(BaseModel):
    random_filter: bool = True
    select_all: bool = False
    max_recipients: int = 5
    recipient_mode: str = "count"  # "count" | "select_all" | "shortcut"
    shortcut_emoji: Optional[str] = None
    device_id: Optional[str] = None

@app.post("/api/workflow/snap")
async def start_snap_workflow(req: SnapWorkflowRequest):
    dev_id = _resolve_device_id(req.device_id)
    if not adb_service.list_devices():
        asyncio.create_task(demo_engine.run_demo_snap(req.random_filter, req.select_all))
        return {"status": "started", "random_filter": req.random_filter, "device_id": "simulated"}

    asyncio.create_task(auto_snap_engine.run_snap_workflow(
        device_id=dev_id,
        random_filter=req.random_filter,
        select_all=req.select_all,
        max_recipients=req.max_recipients,
        recipient_mode=req.recipient_mode,
        shortcut_emoji=req.shortcut_emoji
    ))
    return {"status": "started", "random_filter": req.random_filter, "device_id": dev_id}

class SnapscoreWorkflowRequest(BaseModel):
    cycles: int = 3
    select_all: bool = False
    max_recipients: int = 5
    recipient_mode: str = "count"  # "count" | "select_all" | "shortcut"
    shortcut_emoji: Optional[str] = None
    cooldown_seconds: int = 15
    device_id: Optional[str] = None

@app.post("/api/workflow/snapscore")
async def start_snapscore_workflow(req: SnapscoreWorkflowRequest):
    dev_id = _resolve_device_id(req.device_id)
    if not adb_service.list_devices():
        asyncio.create_task(demo_engine.run_demo_snapscore(req.cycles))
        return {"status": "started", "cycles": req.cycles, "device_id": "simulated"}

    asyncio.create_task(snapscore_engine.run_booster_workflow(
        device_id=dev_id,
        cycles=req.cycles,
        select_all=req.select_all,
        max_recipients=req.max_recipients,
        recipient_mode=req.recipient_mode,
        shortcut_emoji=req.shortcut_emoji,
        cooldown_seconds=req.cooldown_seconds
    ))
    return {"status": "started", "cycles": req.cycles, "device_id": dev_id}

class ChainedWorkflowRequest(BaseModel):
    routine_type: str = "morning"  # "morning" | "score_and_clean" | "all_in_one" | "custom"
    custom_steps: Optional[List[Dict[str, Any]]] = None
    device_id: Optional[str] = None

@app.post("/api/workflow/chain")
async def start_chained_workflow(req: ChainedWorkflowRequest):
    dev_id = _resolve_device_id(req.device_id)
    if not adb_service.list_devices():
        asyncio.create_task(demo_engine.run_demo_chain(req.routine_type))
        return {"status": "started", "routine_type": req.routine_type, "device_id": "simulated"}

    asyncio.create_task(chained_engine.run_chained_routine(
        device_id=dev_id,
        routine_type=req.routine_type,
        custom_steps=req.custom_steps
    ))
    return {"status": "started", "routine_type": req.routine_type, "device_id": dev_id}



@app.get("/api/logs", response_model=List[AuditLogEntry])
async def get_audit_logs(limit: int = Query(50, le=200)):
    return audit_logger.get_logs(limit=limit)

@app.delete("/api/logs")
async def clear_audit_logs():
    audit_logger.clear()
    await ws_hub.broadcast_to_clients({"type": "LOGS_CLEARED"})
    return {"status": "ok"}

# ----------------- WebSocket Endpoints ----------------- #

@app.websocket("/ws/client")
async def client_websocket_endpoint(websocket: WebSocket):
    await ws_hub.connect_client(websocket)
    try:
        # Send initial status
        adb_devs = adb_service.list_devices()
        ws_devs = ws_hub.get_all_devices()
        all_devs = {d.device_id: d for d in ws_devs}
        for d in adb_devs:
            if d.device_id not in all_devs:
                all_devs[d.device_id] = d
        snap_ver = "14.29.0.50"
        for d in all_devs.values():
            if getattr(d, "snapchat_version", None):
                snap_ver = d.snapchat_version
                break

        await websocket.send_text(json.dumps({
            "type": "INITIAL_STATE",
            "payload": {
                "state": state_machine.current_state.value,
                "workflow": state_machine.current_workflow,
                "is_paused": state_machine.is_paused,
                "is_stopped": state_machine.is_stopped,
                "snapchat_version": snap_ver,
                "contacts": [c.model_dump() for c in contact_service.get_contacts()],
                "logs": [l.model_dump() for l in audit_logger.get_logs(20)],
                "devices": [d.model_dump() for d in all_devs.values()]
            }
        }))
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                msg_type = msg.get("type")
                if msg_type == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
                elif msg_type == "EMERGENCY_STOP":
                    state_machine.request_stop()
                    await ws_hub.send_command_to_devices({"command": "STOP"})
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_hub.disconnect_client(websocket)

@app.websocket("/ws/device")
async def device_websocket_endpoint(websocket: WebSocket, device_id: str = "android_device"):
    await ws_hub.connect_device(device_id, websocket)
    try:
        while True:
            data_text = await websocket.receive_text()
            try:
                msg = json.loads(data_text)
                msg_type = msg.get("type")
                if msg_type == "DEVICE_HELLO":
                    ws_hub.update_device_info(device_id, msg.get("payload", {}))
                    entry = audit_logger.log(
                        workflow="Device Link",
                        result=ResultStatus.COMPLETED,
                        reason_code="DEVICE_REGISTERED",
                        message=f"Android Device '{device_id}' registered with AccessibilityService"
                    )
                    await ws_hub.broadcast_audit_log(entry)
                elif msg_type == "ACTION_RESULT":
                    status_str = msg.get("status", "UNKNOWN")
                    reason_code = msg.get("reason_code", "DEVICE_EVENT")
                    message = msg.get("message", "Device executed action")

                    # If mobile device triggered Emergency STOP while a workflow is active, halt state machine
                    if reason_code == "USER_EMERGENCY_STOP" and state_machine.current_state == AppState.RUNNING:
                        state_machine.request_stop(reason=f"Mobile Device: {message}")

                    parsed_status = ResultStatus.UNKNOWN
                    try:
                        parsed_status = ResultStatus(status_str)
                    except Exception:
                        pass

                    entry = audit_logger.log(
                        workflow="Device Action",
                        result=parsed_status,
                        reason_code=reason_code,
                        message=message
                    )
                    await ws_hub.broadcast_audit_log(entry)
                elif msg_type == "EMERGENCY_STOP":
                    state_machine.request_stop(reason="Mobile Device pressed Emergency STOP")
                    entry = audit_logger.log(
                        workflow="Device Action",
                        result=ResultStatus.CANCELLED,
                        reason_code="USER_EMERGENCY_STOP",
                        message="Mobile Device pressed Emergency STOP button"
                    )
                    await ws_hub.broadcast_audit_log(entry)
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_hub.disconnect_device(device_id)
