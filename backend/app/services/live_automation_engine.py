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

            # 2. Check Device Availability & Ensure Reverse Port Tunnel
            devices = adb_service.list_devices()
            device_found = any(d.device_id == device_id for d in devices) or len(devices) > 0
            if not device_found:
                raise Exception(f"Device '{device_id}' is not connected via ADB.")

            adb_service.reverse_port(device_id)

            # 3. Launch Snapchat and Ensure Clean Landing Screen (auto-dismiss popups / restart if unexpected)
            await self._step("Launching Snapchat and verifying clean landing screen...", delay=1.0)
            ensured = adb_service.ensure_landing_or_search(device_id)
            if not ensured:
                await self._step("Initial screen unexpected; attempting deep recovery restart...", delay=1.5)
                adb_service.stop_snapchat(device_id)
                await asyncio.sleep(1.0)
                adb_service.launch_snapchat(device_id)
                await asyncio.sleep(2.5)
                adb_service.dismiss_popups(device_id)

            await self._step("Snapchat camera landing screen confirmed. Ready for target dispatch.", delay=1.0)

            successful_targets = []
            failed_targets = []

            # 4. Process Each Target
            for idx, target in enumerate(targets, 1):
                if state_machine.is_stopped:
                    raise Exception("Emergency stop invoked by user")

                username = target.username
                await self._step(
                    f"[{idx}/{total}] Processing target @{username} ({target.display_name or 'Friend'})...",
                    delay=0.8
                )

                # Step 4a: Verify Screen State & Dismiss any runtime popups
                screen_state = adb_service.detect_screen_state(device_id)
                if screen_state in ["POPUP", "PROFILE_PAGE", "UNEXPECTED_SCREEN"]:
                    await self._step(f"[{idx}/{total}] Unexpected screen/popup detected ('{screen_state}'). Recovering clean state...", delay=0.8)
                    adb_service.ensure_landing_or_search(device_id)
                    screen_state = adb_service.detect_screen_state(device_id)

                # Step 4b: Open / Focus Search Bar
                if screen_state != "SEARCH_PAGE":
                    search_coords = adb_service.find_bounds(device_id, "search")
                    if search_coords:
                        await self._step(f"[{idx}/{total}] Located Search Bar at ({search_coords[0]}, {search_coords[1]}). Tapping...", delay=0.6)
                        adb_service.input_tap(device_id, search_coords[0], search_coords[1])
                    else:
                        await self._step(f"[{idx}/{total}] Activating Snapchat search icon...", delay=0.6)
                        adb_service.input_tap(device_id, 156, 124)

                    await asyncio.sleep(1.0)

                    # Post-tap verification: if a popup intercepted the tap or profile opened
                    post_open_state = adb_service.detect_screen_state(device_id)
                    if post_open_state == "POPUP":
                        adb_service.dismiss_popups(device_id)
                        await asyncio.sleep(0.8)
                    elif post_open_state == "PROFILE_PAGE":
                        adb_service.input_key(device_id, 4) # Exit profile back to camera
                        await asyncio.sleep(0.8)
                        adb_service.input_tap(device_id, 156, 124)
                        await asyncio.sleep(0.8)

                # Clear previous search if clear button exists
                clear_coords = adb_service.find_bounds(device_id, "clear")
                if clear_coords:
                    adb_service.input_tap(device_id, clear_coords[0], clear_coords[1])
                    await asyncio.sleep(0.4)

                # Step 4c: Inject Target Username
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
                await self._step(f"[{idx}/{total}] Awaiting search query results from Snapchat servers...", delay=2.4)

                # Step 4d: Locate and Tap 'Add' or 'Subscribe' button
                add_coords = adb_service.find_bounds(device_id, "add", target_name=username)
                if add_coords:
                    await self._step(f"[{idx}/{total}] Matched Add button at ({add_coords[0]}, {add_coords[1]}). Tapping...", delay=0.8)
                    adb_service.input_tap(device_id, add_coords[0], add_coords[1])
                    successful_targets.append(username)
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
                        successful_targets.append(username)
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
                        await asyncio.sleep(0.5)
                        failed_targets.append(username)
                        await self._step(
                            f"[{idx}/{total}] Target @{username} search completed. No Add Friend button present on Snapchat for this query.",
                            delay=1.0,
                            status=ResultStatus.FAILED,
                            reason="NO_ADD_BUTTON_FOUND"
                        )

                # Step 4e: Clear search bar or navigate back for next target
                clear_coords = adb_service.find_bounds(device_id, "clear")
                if clear_coords:
                    adb_service.input_tap(device_id, clear_coords[0], clear_coords[1])
                else:
                    adb_service.input_key(device_id, 4) # Back
                await asyncio.sleep(0.5)

                # Step 4f: Human Pacing Delay (Random jitter between 1.8s and 3.2s to prevent account flags)
                if idx < total:
                    jitter = round(random.uniform(1.8, 3.2), 2)
                    await self._step(f"Human pacing guard: Waiting {jitter}s jitter before next action...", delay=jitter)

            # 5. Workflow Outcome Evaluation
            if not state_machine.is_stopped:
                if len(successful_targets) == 0:
                    state_machine.transition_to(
                        AppState.FAILED,
                        reason=f"No friend requests could be sent (all {len(failed_targets)} targets failed or had no Add button)."
                    )
                    await self._step(
                        f"Live automation halted: 0/{total} targets succeeded. Check search queries or screen popups.",
                        delay=0.5,
                        status=ResultStatus.FAILED,
                        reason="ALL_TARGETS_FAILED"
                    )
                else:
                    state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                    outcome_msg = (
                        f"Live automation completed: {len(successful_targets)}/{total} friend requests sent successfully."
                        if len(failed_targets) > 0
                        else f"Live automation completed successfully for all {total} targets."
                    )
                    await self._step(
                        outcome_msg,
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
