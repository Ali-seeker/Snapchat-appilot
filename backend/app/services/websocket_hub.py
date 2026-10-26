import json
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket
from ..models.schemas import AppState, AuditLogEntry, DeviceInfo

class WebSocketHub:
    def __init__(self):
        self._clients: Set[WebSocket] = set()
        self._devices: Dict[str, WebSocket] = {}
        self._device_info: Dict[str, DeviceInfo] = {}

    async def connect_client(self, websocket: WebSocket):
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect_client(self, websocket: WebSocket):
        self._clients.discard(websocket)

    async def connect_device(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self._devices[device_id] = websocket
        if device_id not in self._device_info:
            self._device_info[device_id] = DeviceInfo(
                device_id=device_id,
                model="Android Companion",
                is_connected=True
            )
        else:
            self._device_info[device_id].is_connected = True

        await self.broadcast_to_clients({
            "type": "DEVICE_CONNECTED",
            "payload": self._device_info[device_id].model_dump()
        })

    def disconnect_device(self, device_id: str):
        if device_id in self._devices:
            del self._devices[device_id]
        if device_id in self._device_info:
            self._device_info[device_id].is_connected = False

    def update_device_info(self, device_id: str, updates: Dict[str, Any]):
        if device_id in self._device_info:
            current = self._device_info[device_id].model_dump()
            current.update(updates)
            self._device_info[device_id] = DeviceInfo(**current)

    def get_all_devices(self) -> list[DeviceInfo]:
        return list(self._device_info.values())

    async def broadcast_to_clients(self, message: Dict[str, Any]):
        disconnected = []
        for client in self._clients:
            try:
                await client.send_text(json.dumps(message))
            except Exception:
                disconnected.append(client)
        for d in disconnected:
            self._clients.discard(d)

    async def broadcast_state(self, state: AppState, workflow: Optional[str] = None):
        await self.broadcast_to_clients({
            "type": "STATE_CHANGE",
            "payload": {
                "state": state.value,
                "workflow": workflow
            }
        })

    async def broadcast_audit_log(self, entry: AuditLogEntry):
        await self.broadcast_to_clients({
            "type": "AUDIT_LOG",
            "payload": entry.model_dump()
        })

    async def send_command_to_devices(self, command: Dict[str, Any]):
        disconnected = []
        for dev_id, ws in self._devices.items():
            try:
                await ws.send_text(json.dumps(command))
            except Exception:
                disconnected.append(dev_id)
        for dev_id in disconnected:
            self.disconnect_device(dev_id)

ws_hub = WebSocketHub()
