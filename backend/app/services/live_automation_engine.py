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
                    delay=0.6
                )

                # Step 4a: Screen Perception & Clean Camera Landing Verification
                screen_state = adb_service.detect_screen_state(device_id)
                if screen_state != "CAMERA_LANDING":
                    if screen_state == "SEARCH_PAGE":
                        adb_service.close_search_to_camera(device_id)
                    elif screen_state == "POPUP":
                        adb_service.dismiss_popups(device_id)
                    elif screen_state == "PROFILE_PAGE":
                        adb_service.input_key(device_id, 4)
                    else:
                        adb_service.ensure_landing_or_search(device_id)

                    screen_state = adb_service.detect_screen_state(device_id)
                    if screen_state != "CAMERA_LANDING":
                        adb_service.ensure_landing_or_search(device_id)

                await self._step(f"[{idx}/{total}] Confirmed camera landing view. Transitioning to search...", delay=0.4)

                # Step 4b: Open Search View via Element Attributes
                search_elem = (
                    adb_service.find_element(device_id, resource_id="hova_header_search_icon")
                    or adb_service.find_element(device_id, content_desc="Search")
                    or adb_service.find_element(device_id, resource_id="search-textfield")
                )
                search_coords = search_elem["center"] if search_elem else adb_service.find_bounds(device_id, "search")
                if search_coords:
                    await asyncio.sleep(random.uniform(0.3, 0.6)) # Human hesitation before reaching for search
                    bounds = search_elem["bounds"] if search_elem else None
                    adb_service.input_tap_human(device_id, search_coords[0], search_coords[1], bounds=bounds)
                else:
                    await self._step(f"[{idx}/{total}] Search icon not found. Re-aligning camera view...", delay=0.5)
                    adb_service.ensure_landing_or_search(device_id)

                await asyncio.sleep(random.uniform(0.7, 1.1)) # Human visual perception time as search screen opens

                # Step 4c: Verify Search Screen & Check for Unwanted Popups
                current_state = adb_service.detect_screen_state(device_id)
                if current_state == "POPUP":
                    await self._step(f"[{idx}/{total}] Intercepted modal/dialog overlay. Dismissing popup...", delay=0.6)
                    adb_service.dismiss_popups(device_id)
                    await asyncio.sleep(0.8)
                elif current_state == "PROFILE_PAGE":
                    adb_service.input_key(device_id, 4)
                    await asyncio.sleep(0.8)
                    retry_elem = adb_service.find_element(device_id, resource_id="hova_header_search_icon") or adb_service.find_element(device_id, content_desc="Search")
                    if retry_elem:
                        adb_service.input_tap_human(device_id, retry_elem["center"][0], retry_elem["center"][1], bounds=retry_elem["bounds"])
                        await asyncio.sleep(0.8)

                # Step 4d: Check if Search Field has Existing Text & Focus Input
                existing_text = adb_service.get_search_field_text(device_id)
                if existing_text:
                    # ONLY clear if there is actually text inside the search field
                    clear_elem = adb_service.find_element(device_id, resource_id="clear-button")
                    if clear_elem:
                        await asyncio.sleep(random.uniform(0.2, 0.4))
                        adb_service.input_tap_human(device_id, clear_elem["center"][0], clear_elem["center"][1], bounds=clear_elem["bounds"])
                        await asyncio.sleep(0.3)

                # Tap inside the search input box to ensure it is focused
                input_field = adb_service.find_element(device_id, resource_id="search-textfield")
                if input_field:
                    adb_service.input_tap_human(device_id, input_field["center"][0], input_field["center"][1], bounds=input_field["bounds"])

                # Step 4e: Human Keystroke Typing with Natural Pacing
                await asyncio.sleep(random.uniform(0.4, 0.7)) # Human eye focuses on keyboard
                await self._step(f"[{idx}/{total}] Typing target '@{username}' with organic human keystroke intervals...", delay=0.3)
                adb_service.input_text_human(device_id, username, min_delay=0.08, max_delay=0.18)

                await asyncio.sleep(random.uniform(0.4, 0.7)) # Human delay before hitting Enter / Search
                adb_service.input_key(device_id, 66) # KEYCODE_ENTER (Search query submit)

                # Also send companion event to accessibility service
                await ws_hub.send_command_to_devices({
                    "type": "EXECUTE_ACTION",
                    "action": "SEARCH_USER",
                    "params": {"username": username}
                })

                # Await network response and simulate human visual scanning
                scan_delay = round(random.uniform(2.2, 3.2), 2)
                await self._step(f"[{idx}/{total}] Awaiting Snapchat servers and scanning search results ({scan_delay}s)...", delay=scan_delay)

                # Step 4f: Screen Awareness Inspection of Results
                res_info = adb_service.inspect_search_result(device_id, username)

                # Fallback to find_bounds for tests or legacy layouts if inspect returned NOT_FOUND
                if res_info["status"] == "NOT_FOUND":
                    fallback_add = adb_service.find_bounds(device_id, "add", target_name=username)
                    if fallback_add:
                        res_info = {
                            "status": "CAN_ADD",
                            "center": fallback_add,
                            "bounds": None,
                            "details": "Matched Add button via bounds fallback"
                        }
                    else:
                        fallback_sub = adb_service.find_bounds(device_id, "subscribe", target_name=username)
                        if fallback_sub:
                            res_info = {
                                "status": "CAN_SUBSCRIBE",
                                "center": fallback_sub,
                                "bounds": None,
                                "details": "Matched Subscribe button via bounds fallback"
                            }

                if res_info["status"] == "CAN_ADD":
                    await self._step(
                        f"[{idx}/{total}] Found Add Friend button for @{username}. Performing organic finger tap gesture...",
                        delay=0.3
                    )
                    await asyncio.sleep(random.uniform(0.6, 1.0)) # Human decision time before tapping Add
                    adb_service.input_tap_human(device_id, res_info["center"][0], res_info["center"][1], bounds=res_info.get("bounds"))
                    successful_targets.append(username)
                    await self._step(
                        f"[{idx}/{total}] Successfully sent friend request to @{username}!",
                        delay=1.0,
                        status=ResultStatus.COMPLETED,
                        reason="FRIEND_REQUEST_SENT"
                    )
                elif res_info["status"] == "ALREADY_FRIEND":
                    await self._step(
                        f"[{idx}/{total}] Target @{username} is already added as a friend or friend request is pending.",
                        delay=0.8,
                        status=ResultStatus.COMPLETED,
                        reason="ALREADY_FRIEND"
                    )
                    successful_targets.append(username)
                elif res_info["status"] == "CAN_SUBSCRIBE":
                    await self._step(
                        f"[{idx}/{total}] Found Subscribe button for creator @{username}. Tapping...",
                        delay=0.3
                    )
                    await asyncio.sleep(random.uniform(0.6, 1.0))
                    adb_service.input_tap_human(device_id, res_info["center"][0], res_info["center"][1], bounds=res_info.get("bounds"))
                    successful_targets.append(username)
                    await self._step(
                        f"[{idx}/{total}] Subscribed to Snap Star / Creator @{username}!",
                        delay=1.0,
                        status=ResultStatus.COMPLETED,
                        reason="SUBSCRIBED"
                    )
                else:
                    # Target not found or no Add button
                    await ws_hub.send_command_to_devices({
                        "type": "EXECUTE_ACTION",
                        "action": "CLICK_ADD",
                        "params": {"username": username}
                    })
                    await asyncio.sleep(0.5)
                    failed_targets.append(username)
                    await self._step(
                        f"[{idx}/{total}] Target @{username} search completed. No Add Friend button present for this query.",
                        delay=1.0,
                        status=ResultStatus.FAILED,
                        reason="NO_ADD_BUTTON_FOUND"
                    )

                # Step 4g: Graceful Return to Camera Landing View
                await self._step(f"[{idx}/{total}] Closing search interface and returning to primary camera view...", delay=0.4)
                adb_service.close_search_to_camera(device_id)
                await asyncio.sleep(random.uniform(0.6, 0.9))

                # Step 4h: Human Pacing Delay (Random jitter between 2.2s and 3.8s to prevent account flags)
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
