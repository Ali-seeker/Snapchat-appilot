import json
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any
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
    yield

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
    return {
        "state": state_machine.current_state.value,
        "workflow": state_machine.current_workflow,
        "is_paused": state_machine.is_paused,
        "is_stopped": state_machine.is_stopped,
        "adb_available": adb_service.is_adb_available(),
        "devices": ws_hub.get_all_devices()
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
        await websocket.send_text(json.dumps({
            "type": "INITIAL_STATE",
            "payload": {
                "state": state_machine.current_state.value,
                "workflow": state_machine.current_workflow,
                "is_paused": state_machine.is_paused,
                "is_stopped": state_machine.is_stopped,
                "contacts": [c.model_dump() for c in contact_service.get_contacts()],
                "logs": [l.model_dump() for l in audit_logger.get_logs(20)],
                "devices": [d.model_dump() for d in ws_hub.get_all_devices()]
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

                    # If mobile device triggered Emergency STOP, halt state machine immediately
                    if reason_code == "USER_EMERGENCY_STOP" or status_str == "CANCELLED":
                        state_machine.request_stop(reason=f"Mobile Device: {message}")

                    entry = audit_logger.log(
                        workflow="Device Action",
                        result=ResultStatus(status_str),
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
