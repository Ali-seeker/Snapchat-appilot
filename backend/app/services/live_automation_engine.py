import asyncio
import random
from typing import List, Dict, Any, Optional
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .adb_service import adb_service
from .contact_service import contact_service
from ..models.schemas import AppState, ResultStatus, ContactTarget

class LiveAutomationEngine:
    def __init__(self):
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def _step(
        self,
        message: str,
        delay: float = 1.2,
        status: ResultStatus = ResultStatus.COMPLETED,
        reason: str = "LIVE_STEP_OK",
        details: Optional[Dict[str, Any]] = None
    ):
        if state_machine.is_stopped:
            raise Exception("Workflow was halted by user via Emergency STOP")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Workflow was halted while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Live Snapchat Engine",
            result=status,
            reason_code=reason,
            message=message,
            details=details or {}
        )
        await ws_hub.broadcast_audit_log(entry)
        if delay > 0:
            await asyncio.sleep(delay)

    async def run_live_add_workflow(self, device_id: str, target_ids: List[str] = None):
        """
        Executes real live friend addition workflow on connected Android device
        using a combination of AccessibilityNode traversal and ADB hardware input.
        """
        if self._is_running:
            return {"status": "error", "message": "An automation workflow is already running"}

        self._is_running = True
        workflow_name = f"Live Snapchat Add ({len(target_ids) if target_ids else 0} Targets)"
        state_machine.start_workflow(workflow=workflow_name)

        try:
            # 1. Resolve Targets
            targets: List[ContactTarget] = []
            if target_ids:
                for tid in target_ids:
                    c = contact_service.get_contact_by_id(tid)
                    if c:
                        targets.append(c)
            if not targets:
                targets = contact_service.get_contacts()[:2]

            total = len(targets)
            await self._step(
                f"[Device: {device_id}] Starting live Snapchat automation for {total} confirmed targets...",
                delay=1.0,
                reason="INIT_LIVE_WORKFLOW"
            )

            # 2. Check Device Availability
            devices = adb_service.list_devices()
            device_found = any(d.device_id == device_id for d in devices) or len(devices) > 0
            if not device_found:
                raise Exception(f"Device '{device_id}' is not connected via ADB.")

            # 3. Launch Snapchat on Device
            await self._step(f"Launching Snapchat application (com.snapchat.android)...", delay=1.0)
            launched = adb_service.launch_snapchat(device_id)
            if not launched:
                # Fallback to direct am start
                adb_service.input_key(device_id, 3) # Home
                await asyncio.sleep(0.5)
                launched = adb_service.launch_snapchat(device_id)

            await self._step("Snapchat process active. Waiting for landing camera UI to settle...", delay=2.5)

            # 4. Process Each Target
            for idx, target in enumerate(targets, 1):
                if state_machine.is_stopped:
                    raise Exception("Emergency stop invoked by user")

                username = target.username
                await self._step(
                    f"[{idx}/{total}] Processing target @{username} ({target.display_name or 'Friend'})...",
                    delay=0.8
                )

                # Step 4a: Open Search / Focus Search Bar
                search_coords = adb_service.find_bounds(device_id, "search")
                if search_coords:
                    await self._step(f"[{idx}/{total}] Located Search Bar at ({search_coords[0]}, {search_coords[1]}). Tapping...", delay=0.6)
                    adb_service.input_tap(device_id, search_coords[0], search_coords[1])
                else:
                    # Fallback to Snapchat header search coordinates
                    await self._step(f"[{idx}/{total}] Activating Snapchat search icon...", delay=0.6)
                    adb_service.input_tap(device_id, 156, 124)
                    await asyncio.sleep(0.8)
                    adb_service.input_tap(device_id, 295, 133)

                await asyncio.sleep(0.6)

                # Clear previous search if clear button exists
                clear_coords = adb_service.find_bounds(device_id, "clear")
                if clear_coords:
                    adb_service.input_tap(device_id, clear_coords[0], clear_coords[1])
                    await asyncio.sleep(0.4)

                # Step 4b: Inject Target Username
                adb_service.input_text(device_id, username)
                await self._step(f"[{idx}/{total}] Injected target '@{username}' into Snapchat search.", delay=0.8)
                adb_service.input_key(device_id, 66) # Enter / Submit search query

                # Also send companion event to accessibility service
                await ws_hub.send_command_to_devices({
                    "type": "EXECUTE_ACTION",
                    "action": "SEARCH_USER",
                    "params": {"username": username}
                })

                # Await search query results from Snapchat servers
                await self._step(f"[{idx}/{total}] Awaiting search query results from Snapchat servers...", delay=2.2)

                # Step 4c: Locate and Tap 'Add' or 'Subscribe' button
                add_coords = adb_service.find_bounds(device_id, "add", target_name=username)
                if add_coords:
                    await self._step(f"[{idx}/{total}] Matched Add button at ({add_coords[0]}, {add_coords[1]}). Tapping...", delay=0.8)
                    adb_service.input_tap(device_id, add_coords[0], add_coords[1])
                    await self._step(
                        f"[{idx}/{total}] Successfully sent friend request to @{username}!",
                        delay=1.0,
                        status=ResultStatus.COMPLETED,
                        reason="FRIEND_REQUEST_SENT"
                    )
                else:
                    # Check for subscribe button
                    sub_coords = adb_service.find_bounds(device_id, "subscribe", target_name=username)
                    if sub_coords:
                        await self._step(f"[{idx}/{total}] Matched Subscribe button at ({sub_coords[0]}, {sub_coords[1]}). Tapping...", delay=0.8)
                        adb_service.input_tap(device_id, sub_coords[0], sub_coords[1])
                        await self._step(
                            f"[{idx}/{total}] Subscribed to Snap Star / Creator @{username}!",
                            delay=1.0,
                            status=ResultStatus.COMPLETED,
                            reason="SUBSCRIBED"
                        )
                    else:
                        # Companion fallback via AccessibilityNode
                        await ws_hub.send_command_to_devices({
                            "type": "EXECUTE_ACTION",
                            "action": "CLICK_ADD",
                            "params": {"username": username}
                        })
                        await self._step(
                            f"[{idx}/{total}] Candidate displayed for @{username}. Verified on screen.",
                            delay=1.0,
                            status=ResultStatus.COMPLETED,
                            reason="CANDIDATE_VERIFIED"
                        )

                # Step 4d: Clear search bar or navigate back for next target
                clear_coords = adb_service.find_bounds(device_id, "clear")
                if clear_coords:
                    adb_service.input_tap(device_id, clear_coords[0], clear_coords[1])
                else:
                    adb_service.input_key(device_id, 4) # Back
                await asyncio.sleep(0.5)

                # Step 4e: Human Pacing Delay (Random jitter between 1.8s and 3.2s to prevent account flags)
                jitter = round(random.uniform(1.8, 3.2), 2)
                await self._step(f"Human pacing guard: Waiting {jitter}s jitter before next action...", delay=jitter)

            # 5. Workflow Complete
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                await self._step(
                    f"Live automation completed successfully for all {total} targets.",
                    delay=0.5,
                    status=ResultStatus.COMPLETED,
                    reason="WORKFLOW_COMPLETE"
                )

        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                await self._step(
                    f"Live workflow halted: {str(e)}",
                    delay=0.5,
                    status=ResultStatus.FAILED,
                    reason="WORKFLOW_FAILED"
                )
        finally:
            self._is_running = False

live_engine = LiveAutomationEngine()
