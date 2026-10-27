import asyncio
import random
from typing import List, Dict, Any, Optional
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .adb_service import adb_service
from ..models.schemas import AppState, ResultStatus

class AutoSnapEngine:
    def __init__(self):
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def _step(
        self,
        message: str,
        delay: float = 1.0,
        status: ResultStatus = ResultStatus.COMPLETED,
        reason: str = "SNAP_STEP_OK",
        details: Optional[Dict[str, Any]] = None
    ):
        if state_machine.is_stopped:
            raise Exception("Workflow was halted by user via Emergency STOP")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Workflow was halted while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Auto Snap Engine",
            result=status,
            reason_code=reason,
            message=message,
            details=details or {}
        )
        await ws_hub.broadcast_audit_log(entry)
        if delay > 0:
            await asyncio.sleep(delay)

    async def run_snap_workflow(
        self,
        device_id: str,
        random_filter: bool = True,
        select_all: bool = True,
        max_recipients: int = 15
    ):
        if self._is_running:
            return {"status": "error", "message": "An automation workflow is already running"}

        self._is_running = True
        workflow_name = "Auto Snap Dispatch"
        state_machine.start_workflow(workflow=workflow_name)

        try:
            # 1. Device connection check & tunnel
            devices = adb_service.list_devices()
            dev_found = any(d.device_id == device_id for d in devices) or len(devices) > 0
            if not dev_found:
                raise Exception(f"Device '{device_id}' is not connected via ADB.")

            adb_service.reverse_port(device_id)

            # 2. Interruption resilience
            adb_service.dismiss_heads_up_notification(device_id)
            adb_service.dismiss_popups(device_id)

            # 3. Ensure Camera Landing
            await self._step("Verifying clean Snapchat camera landing screen...", delay=0.8)
            adb_service.ensure_landing_or_search(device_id)

            # 4. Capture Snap Photo
            await self._step("Triggering camera hardware shutter to capture Snap...", delay=0.4)
            adb_service.capture_snap_photo(device_id)
            await asyncio.sleep(1.2) # Wait for preview UI to render

            # 5. Apply Random Filter (Artistic lens / Color overlay)
            if random_filter:
                swipes = random.randint(1, 3)
                await self._step(f"Applying random aesthetic filter ({swipes} lens swipe gestures)...", delay=0.4)
                adb_service.apply_random_filter(device_id, swipes_count=swipes)
                await asyncio.sleep(0.8)

            # 6. Open Send To Screen
            await self._step("Transitioning to 'Send To' recipient selection screen...", delay=0.6)
            adb_service.open_send_to_screen(device_id)
            await asyncio.sleep(1.2)

            # 7. Select Recipients & Send
            mode_desc = "All Available Friends" if select_all else f"Top {max_recipients} Friends"
            await self._step(f"Selecting recipients ({mode_desc}) and dispatching Snap...", delay=0.8)

            sent_count = adb_service.select_recipients_and_send(
                device_id,
                select_all=select_all,
                max_recipients=max_recipients
            )

            # Interruption check
            adb_service.dismiss_heads_up_notification(device_id)

            # 8. Complete & Verify Camera Return
            await self._step(f"Snap successfully sent to {sent_count} recipient(s)!", delay=1.0, reason="SNAP_SENT")

            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                await self._step("Returned to camera landing. Auto Snap workflow complete.", delay=0.5, reason="WORKFLOW_COMPLETE")

            return {"status": "ok", "recipients_count": sent_count}

        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                await self._step(
                    f"Auto Snap halted: {str(e)}",
                    delay=0.5,
                    status=ResultStatus.FAILED,
                    reason="SNAP_WORKFLOW_FAILED"
                )
            return {"status": "error", "message": str(e)}
        finally:
            self._is_running = False

auto_snap_engine = AutoSnapEngine()
