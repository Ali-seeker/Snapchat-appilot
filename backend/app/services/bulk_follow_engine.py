import asyncio
import random
from typing import List, Dict, Any, Optional
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .adb_service import adb_service
from .contact_service import contact_service
from ..models.schemas import AppState, ResultStatus, ContactTarget

class BulkFollowEngine:
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
        reason: str = "FOLLOW_STEP_OK",
        details: Optional[Dict[str, Any]] = None
    ):
        if state_machine.is_stopped:
            raise Exception("Workflow was halted by user via Emergency STOP")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Workflow was halted while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Bulk Follow Engine",
            result=status,
            reason_code=reason,
            message=message,
            details=details or {}
        )
        await ws_hub.broadcast_audit_log(entry)
        if delay > 0:
            await asyncio.sleep(delay)

    async def run_follow_workflow(
        self,
        device_id: str,
        mode: str = "quick_add",  # "search" | "quick_add" | "accept"
        target_ids: Optional[List[str]] = None,
        max_count: int = 10
    ):
        if self._is_running:
            return {"status": "error", "message": "An automation workflow is already running"}

        self._is_running = True
        mode_titles = {
            "search": f"Bulk Search Add ({len(target_ids) if target_ids else 0} Targets)",
            "quick_add": f"Quick Add Suggestions (Target: {max_count})",
            "accept": f"Accept Incoming Requests (Target: {max_count})"
        }
        workflow_name = mode_titles.get(mode, f"Bulk Follow ({mode.upper()})")
        state_machine.start_workflow(workflow=workflow_name)

        try:
            # 1. Device connection verification & reverse tunnel
            devices = adb_service.list_devices()
            dev_found = any(d.device_id == device_id for d in devices) or len(devices) > 0
            if not dev_found:
                raise Exception(f"Device '{device_id}' is not connected via ADB.")

            adb_service.reverse_port(device_id)

            # 2. Interruption resilience: Dismiss any top notifications or stale popups
            adb_service.dismiss_heads_up_notification(device_id)
            adb_service.dismiss_popups(device_id)

            # 3. Mode Branching
            if mode == "quick_add":
                await self._execute_quick_add(device_id, max_count)
            elif mode == "accept":
                await self._execute_accept_incoming(device_id, max_count)
            else:
                await self._execute_search_add(device_id, target_ids or [])

            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                await self._step(
                    f"Bulk follow routine ({mode}) completed successfully.",
                    delay=0.5,
                    reason="FOLLOW_WORKFLOW_COMPLETE"
                )

        except Exception as e:
            print(f"DEBUG EXCEPTION IN BULK FOLLOW: {e!r}")
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                await self._step(
                    f"Bulk follow halted: {str(e)}",
                    delay=0.5,
                    status=ResultStatus.FAILED,
                    reason="FOLLOW_WORKFLOW_FAILED"
                )
        finally:
            self._is_running = False

    async def _execute_quick_add(self, device_id: str, max_count: int):
        await self._step("Navigating to Add Friends & Quick Add suggestions page...", delay=1.0)
        adb_service.ensure_landing_or_search(device_id)
        opened = adb_service.open_add_friends_page(device_id)
        if not opened:
            # Try once more with landing reset
            adb_service.ensure_landing_or_search(device_id)
            adb_service.open_add_friends_page(device_id)

        await self._step(f"Scanning Quick Add suggestions list (Target: up to {max_count})...", delay=0.8)

        total_added = 0
        scroll_attempts = 0
        max_scrolls = 4

        while total_added < max_count and scroll_attempts < max_scrolls:
            if state_machine.is_stopped:
                raise Exception("Halted by Emergency STOP")

            # Check for top notification or popup interruption
            adb_service.dismiss_heads_up_notification(device_id)

            # Add batch from visible screen
            batch_target = min(3, max_count - total_added)
            added_in_batch = adb_service.quick_add_batch(device_id, max_count=batch_target)
            batch_count = len(added_in_batch) if isinstance(added_in_batch, list) else int(added_in_batch or 0)
            total_added += batch_count

            if batch_count > 0:
                await self._step(
                    f"Added {batch_count} suggested friend(s). Total added: {total_added}/{max_count}.",
                    delay=random.uniform(1.2, 1.8),
                    reason="QUICK_ADD_BATCH"
                )

            # Human scroll down to load more suggestions
            if total_added < max_count:
                await self._step("Scrolling down to reveal more suggestions...", delay=0.4)
                adb_service.scroll_down(device_id, distance=450)
                scroll_attempts += 1
                await asyncio.sleep(random.uniform(1.2, 2.0))

        # Return safely to camera landing
        adb_service.input_key(device_id, 4) # Back to camera
        await self._step(f"Quick Add finished: Total {total_added} friend(s) added.", delay=0.6)

    async def _execute_accept_incoming(self, device_id: str, max_count: int):
        await self._step("Opening Add Friends page to check incoming requests ('Added Me')...", delay=1.0)
        adb_service.ensure_landing_or_search(device_id)
        adb_service.open_add_friends_page(device_id)

        await self._step(f"Scanning 'Added Me' incoming friend requests (Target: up to {max_count})...", delay=0.8)
        accepted = adb_service.accept_incoming_requests(device_id, max_count=max_count)
        accepted_count = len(accepted) if isinstance(accepted, list) else int(accepted or 0)

        if accepted_count > 0:
            await self._step(
                f"Successfully accepted {accepted_count} incoming friend request(s)!",
                delay=1.0,
                reason="REQUESTS_ACCEPTED"
            )
        else:
            await self._step(
                "No pending incoming friend requests found under 'Added Me'.",
                delay=0.8,
                status=ResultStatus.SKIPPED,
                reason="NO_INCOMING_REQUESTS"
            )

        # Return safely to camera landing
        adb_service.input_key(device_id, 4)

    async def _execute_search_add(self, device_id: str, target_ids: List[str]):
        # Resolve targets from contact service
        targets: List[ContactTarget] = []
        for tid in target_ids:
            c = contact_service.get_contact_by_id(tid)
            if c:
                targets.append(c)

        if not targets:
            targets = contact_service.get_contacts()[:5]

        total = len(targets)
        await self._step(f"Starting bulk username search & add for {total} targets...", delay=0.8)

        adb_service.ensure_landing_or_search(device_id)

        for idx, target in enumerate(targets, 1):
            if state_machine.is_stopped:
                raise Exception("Halted by Emergency STOP")

            username = target.username
            await self._step(f"[{idx}/{total}] Searching @{username} with human typing rhythm...", delay=0.4)

            # Check for interruptions
            adb_service.dismiss_heads_up_notification(device_id)

            # Open search
            search_elem = (
                adb_service.find_element(device_id, resource_id="hova_header_search_icon")
                or adb_service.find_element(device_id, content_desc="Search")
                or adb_service.find_element(device_id, resource_id="search-textfield")
            )
            search_coords = search_elem["center"] if search_elem else (360, 100)
            adb_service.input_tap_human(device_id, search_coords[0], search_coords[1])
            await asyncio.sleep(0.8)

            # Clear old text if any
            if adb_service.get_search_field_text(device_id):
                clear_elem = adb_service.find_element(device_id, resource_id="clear-button")
                if clear_elem:
                    adb_service.input_tap_human(device_id, clear_elem["center"][0], clear_elem["center"][1])
                    await asyncio.sleep(0.3)

            # Type username
            adb_service.input_text_human(device_id, username, min_delay=0.08, max_delay=0.18)
            await asyncio.sleep(0.5)
            adb_service.input_key(device_id, 66) # Submit

            # Await results
            await asyncio.sleep(random.uniform(2.0, 3.0))
            res_info = adb_service.inspect_search_result(device_id, username)

            if res_info["status"] == "CAN_ADD":
                await asyncio.sleep(random.uniform(0.6, 1.0))
                adb_service.input_tap_human(device_id, res_info["center"][0], res_info["center"][1])
                await self._step(f"[{idx}/{total}] Added @{username} successfully!", delay=0.8, reason="FRIEND_ADDED")
            elif res_info["status"] == "ALREADY_FRIEND":
                await self._step(f"[{idx}/{total}] @{username} is already added or pending.", delay=0.6, reason="ALREADY_FRIEND")
            elif res_info["status"] == "CAN_SUBSCRIBE":
                adb_service.input_tap_human(device_id, res_info["center"][0], res_info["center"][1])
                await self._step(f"[{idx}/{total}] Subscribed to creator @{username}!", delay=0.8, reason="SUBSCRIBED")
            else:
                await self._step(f"[{idx}/{total}] @{username} not found or no add button.", delay=0.6, status=ResultStatus.SKIPPED, reason="TARGET_NOT_FOUND")

            adb_service.close_search_to_camera(device_id)
            if idx < total:
                pause = round(random.uniform(2.0, 3.5), 1)
                await self._step(f"Human pacing guard: resting {pause}s...", delay=pause)

bulk_follow_engine = BulkFollowEngine()
