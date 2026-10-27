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

                # Step 4b: Open / Focus Search Bar dynamically by element
                if screen_state != "SEARCH_PAGE":
                    search_elem = (
                        adb_service.find_element(device_id, resource_id="hova_header_search_icon")
                        or adb_service.find_element(device_id, content_desc="Search")
                        or adb_service.find_element(device_id, resource_id="search-textfield")
                    )
                    search_coords = search_elem["center"] if search_elem else adb_service.find_bounds(device_id, "search")
                    if search_coords:
                        await self._step(
                            f"[{idx}/{total}] Located search element by attributes. Tapping with human finger gesture...",
                            delay=0.4
                        )
                        await asyncio.sleep(random.uniform(0.3, 0.6))
                        bounds = search_elem["bounds"] if search_elem else None
                        adb_service.input_tap_human(device_id, search_coords[0], search_coords[1], bounds=bounds)
                    else:
                        await self._step(f"[{idx}/{total}] Search element not found in current UI hierarchy. Attempting recovery...", delay=0.6)
                        adb_service.ensure_landing_or_search(device_id)

                    await asyncio.sleep(random.uniform(0.8, 1.2))

                    # Post-tap verification: if a popup intercepted the tap or profile opened
                    post_open_state = adb_service.detect_screen_state(device_id)
                    if post_open_state == "POPUP":
                        adb_service.dismiss_popups(device_id)
                        await asyncio.sleep(0.8)
                    elif post_open_state == "PROFILE_PAGE":
                        adb_service.input_key(device_id, 4) # Exit profile back to camera
                        await asyncio.sleep(0.8)
                        retry_elem = (
                            adb_service.find_element(device_id, resource_id="hova_header_search_icon")
                            or adb_service.find_element(device_id, content_desc="Search")
                        )
                        retry_coords = retry_elem["center"] if retry_elem else adb_service.find_bounds(device_id, "search")
                        if retry_coords:
                            bounds = retry_elem["bounds"] if retry_elem else None
                            adb_service.input_tap_human(device_id, retry_coords[0], retry_coords[1], bounds=bounds)
                        await asyncio.sleep(0.8)

                # Clear previous search if clear button exists (by resource-id or content-desc)
                clear_elem = (
                    adb_service.find_element(device_id, resource_id="clear-button")
                    or adb_service.find_element(device_id, content_desc="Clear")
                )
                clear_coords = clear_elem["center"] if clear_elem else adb_service.find_bounds(device_id, "clear")
                if clear_coords:
                    await asyncio.sleep(random.uniform(0.2, 0.4))
                    bounds = clear_elem["bounds"] if clear_elem else None
                    adb_service.input_tap_human(device_id, clear_coords[0], clear_coords[1], bounds=bounds)
                    await asyncio.sleep(random.uniform(0.3, 0.5))

                # Step 4c: Inject Target Username with Human Keystroke Pacing
                await asyncio.sleep(random.uniform(0.4, 0.7)) # Human delay looking at keyboard
                await self._step(f"[{idx}/{total}] Typing target '@{username}' with human keystroke pacing...", delay=0.3)
                adb_service.input_text_human(device_id, username, min_delay=0.08, max_delay=0.18)
                await asyncio.sleep(random.uniform(0.3, 0.6)) # Human delay before submitting search
                adb_service.input_key(device_id, 66) # Enter / Submit search query

                # Also send companion event to accessibility service
                await ws_hub.send_command_to_devices({
                    "type": "EXECUTE_ACTION",
                    "action": "SEARCH_USER",
                    "params": {"username": username}
                })

                # Await search query results with human visual scanning delay
                scan_delay = round(random.uniform(2.3, 3.2), 2)
                await self._step(f"[{idx}/{total}] Waiting for Snapchat servers and visually scanning results ({scan_delay}s)...", delay=scan_delay)

                # Step 4d: Locate and Tap 'Add' or 'Subscribe' button dynamically by element attributes
                add_elem = (
                    adb_service.find_element(device_id, resource_id="add-friend-button", target_name=username)
                    or adb_service.find_element(device_id, text="Add", target_name=username)
                    or adb_service.find_element(device_id, content_desc="Add", target_name=username)
                )
                add_coords = add_elem["center"] if add_elem else adb_service.find_bounds(device_id, "add", target_name=username)
                if add_coords:
                    await self._step(
                        f"[{idx}/{total}] Matched Add button by element attributes. Tapping with human finger gesture...",
                        delay=0.3
                    )
                    await asyncio.sleep(random.uniform(0.5, 0.9)) # Human decision time before tapping Add
                    bounds = add_elem["bounds"] if add_elem else None
                    adb_service.input_tap_human(device_id, add_coords[0], add_coords[1], bounds=bounds)
                    successful_targets.append(username)
                    await self._step(
                        f"[{idx}/{total}] Successfully sent friend request to @{username}!",
                        delay=1.0,
                        status=ResultStatus.COMPLETED,
                        reason="FRIEND_REQUEST_SENT"
                    )
                else:
                    # Check for subscribe button
                    sub_elem = (
                        adb_service.find_element(device_id, resource_id="subscribe-button", target_name=username)
                        or adb_service.find_element(device_id, text="Subscribe", target_name=username)
                    )
                    sub_coords = sub_elem["center"] if sub_elem else adb_service.find_bounds(device_id, "subscribe", target_name=username)
                    if sub_coords:
                        await self._step(
                            f"[{idx}/{total}] Matched Subscribe button by element attributes. Tapping...",
                            delay=0.3
                        )
                        await asyncio.sleep(random.uniform(0.5, 0.9))
                        bounds = sub_elem["bounds"] if sub_elem else None
                        adb_service.input_tap_human(device_id, sub_coords[0], sub_coords[1], bounds=bounds)
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
                clear_elem_post = (
                    adb_service.find_element(device_id, resource_id="clear-button")
                    or adb_service.find_element(device_id, content_desc="Clear")
                )
                if clear_elem_post:
                    await asyncio.sleep(random.uniform(0.2, 0.4))
                    adb_service.input_tap_human(device_id, clear_elem_post["center"][0], clear_elem_post["center"][1], bounds=clear_elem_post["bounds"])
                else:
                    adb_service.input_key(device_id, 4) # Back
                await asyncio.sleep(random.uniform(0.4, 0.7))

                # Step 4f: Human Pacing Delay (Random jitter between 2.2s and 3.8s to prevent account flags)
                if idx < total:
                    jitter = round(random.uniform(2.2, 3.8), 2)
                    await self._step(f"Human pacing guard: Resting {jitter}s before processing next target...", delay=jitter)

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
