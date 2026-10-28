import asyncio
import random
from typing import List, Dict, Any, Optional
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .adb_service import adb_service
from ..models.schemas import AppState, ResultStatus

class BulkUnfollowEngine:
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
        reason: str = "UNFOLLOW_STEP_OK",
        details: Optional[Dict[str, Any]] = None
    ):
        if state_machine.is_stopped:
            raise Exception("Workflow was halted by user via Emergency STOP")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Workflow was halted while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Bulk Unfollow Engine",
            result=status,
            reason_code=reason,
            message=message,
            details=details or {}
        )
        await ws_hub.broadcast_audit_log(entry)
        if delay > 0:
            await asyncio.sleep(delay)

    async def run_unfollow_workflow(
        self,
        device_id: str,
        filter_type: str = "no_streak",  # "no_streak" | "inactive" | "custom"
        days_threshold: int = 17,
        custom_targets: Optional[List[str]] = None,
        max_unfollow: int = 10
    ):
        if self._is_running:
            return {"status": "error", "message": "An automation workflow is already running"}

        self._is_running = True
        filter_labels = {
            "no_streak": "No Streak Filter (🔥 Missing)",
            "inactive": f"Inactivity Filter (Dormant >{days_threshold} Days)",
            "custom": f"Custom Target Unfollow ({len(custom_targets) if custom_targets else 0} Targets)"
        }
        workflow_name = f"Smart Unfollow: {filter_labels.get(filter_type, filter_type.upper())}"
        state_machine.start_workflow(workflow=workflow_name)

        try:
            # 1. Device check & reverse tunnel
            devices = adb_service.list_devices()
            dev_found = any(d.device_id == device_id for d in devices) or len(devices) > 0
            if not dev_found:
                raise Exception(f"Device '{device_id}' is not connected via ADB.")

            adb_service.reverse_port(device_id)

            # Bring Snapchat to foreground deterministically
            adb_service.launch_snapchat(device_id)
            await asyncio.sleep(1.2)

            # 2. Interruption dismissal
            adb_service.dismiss_heads_up_notification(device_id)
            adb_service.dismiss_popups(device_id)

            # 3. Ensure camera landing then open Chat Screen
            await self._step("Transitioning to Snapchat Chat feed...", delay=1.0)
            adb_service.ensure_landing_or_search(device_id)
            adb_service.open_chat_screen(device_id)

            await self._step(f"Scanning friend conversations for criteria: {filter_labels.get(filter_type)}...", delay=1.2)

            total_unfollowed = 0
            scroll_attempts = 0
            max_scrolls = 4

            while total_unfollowed < max_unfollow and scroll_attempts < max_scrolls:
                if state_machine.is_stopped:
                    raise Exception("Halted by Emergency STOP")

                # Interruption resilience
                adb_service.dismiss_heads_up_notification(device_id)

                # Scan current viewport
                candidates = adb_service.scan_chat_friends_and_filter(
                    device_id,
                    filter_type=filter_type,
                    days_threshold=days_threshold
                )

                # If custom targets specified, filter strictly to them
                if filter_type == "custom" and custom_targets:
                    clean_targets = [ct.lower().strip().lstrip("@") for ct in custom_targets]
                    candidates = [c for c in candidates if any(ct in c["name"].lower() for ct in clean_targets)]

                if not candidates:
                    await self._step("No eligible candidates found in visible screen. Scrolling chat feed...", delay=0.6)
                    adb_service.scroll_down(device_id, distance=400)
                    scroll_attempts += 1
                    await asyncio.sleep(random.uniform(1.2, 1.8))
                    continue

                for cand in candidates:
                    if total_unfollowed >= max_unfollow:
                        break
                    if state_machine.is_stopped:
                        raise Exception("Halted by Emergency STOP")

                    friend_name = cand["name"]
                    center = cand["center"]
                    reason_desc = cand["reason"]

                    await self._step(
                        f"Target identified: '{friend_name}' ({reason_desc}). Initiating friend removal...",
                        delay=0.6,
                        reason="UNFOLLOW_CANDIDATE_IDENTIFIED"
                    )

                    # Execute 4-step unfollow
                    success = adb_service.unfollow_friend(device_id, center[0], center[1])
                    if success:
                        total_unfollowed += 1
                        await self._step(
                            f"Successfully unfollowed '{friend_name}'. [Reason: {reason_desc}] ({total_unfollowed}/{max_unfollow})",
                            delay=random.uniform(1.2, 1.8),
                            reason="FRIEND_UNFOLLOWED"
                        )
                        # Anti-ban rest jitter
                        rest = round(random.uniform(2.2, 3.5), 1)
                        await self._step(f"Anti-ban safety pause: resting {rest}s...", delay=rest)
                    else:
                        await self._step(
                            f"Could not open friendship menu for '{friend_name}'. Skipping.",
                            delay=0.5,
                            status=ResultStatus.SKIPPED,
                            reason="UNFOLLOW_SKIPPED"
                        )

                # Scroll down for next batch
                if total_unfollowed < max_unfollow:
                    adb_service.scroll_down(device_id, distance=420)
                    scroll_attempts += 1
                    await asyncio.sleep(random.uniform(1.0, 1.5))

            # Return safely to camera landing
            adb_service.ensure_landing_or_search(device_id)
            await asyncio.sleep(0.5)

            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                await self._step(
                    f"Bulk unfollow routine finished: Total {total_unfollowed} friend(s) removed.",
                    delay=0.5,
                    reason="UNFOLLOW_WORKFLOW_COMPLETE"
                )

        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                await self._step(
                    f"Bulk unfollow halted: {str(e)}",
                    delay=0.5,
                    status=ResultStatus.FAILED,
                    reason="UNFOLLOW_WORKFLOW_FAILED"
                )
        finally:
            self._is_running = False

bulk_unfollow_engine = BulkUnfollowEngine()
