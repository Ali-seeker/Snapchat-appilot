import asyncio
import random
from typing import List, Dict, Any, Optional
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .adb_service import adb_service
from ..models.schemas import AppState, ResultStatus

class SnapscoreEngine:
    """
    Algorithmic Snapscore Acceleration Engine.
    
    Research Findings:
    - Text chats do NOT increase Snapscore (0 points).
    - Photo/Video Snaps sent and opened increase Snapscore (+1 point per snap, plus multi-recipient bonuses).
    - Sending Snaps to multiple friends simultaneously yields multiplicative score growth.
    - Anti-ban safeguards:
      - Random filter variation on every snap
      - 12s - 25s cooldown intervals between dispatch cycles
      - Humanized touch offsets and randomized swipe durations
    """
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
        reason: str = "SNAPSCORE_STEP_OK",
        details: Optional[Dict[str, Any]] = None
    ):
        if state_machine.is_stopped:
            raise Exception("Workflow was halted by user via Emergency STOP")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Workflow was halted while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Snapscore Booster",
            result=status,
            reason_code=reason,
            message=message,
            details=details or {}
        )
        await ws_hub.broadcast_audit_log(entry)
        if delay > 0:
            await asyncio.sleep(delay)

    async def run_booster_workflow(
        self,
        device_id: str,
        cycles: int = 3,
        select_all: bool = True,
        max_recipients: int = 15,
        cooldown_seconds: int = 15
    ):
        if self._is_running:
            return {"status": "error", "message": "An automation workflow is already running"}

        self._is_running = True
        workflow_name = f"Snapscore Booster ({cycles} Cycles)"
        state_machine.start_workflow(workflow=workflow_name)

        try:
            devices = adb_service.list_devices()
            dev_found = any(d.device_id == device_id for d in devices) or len(devices) > 0
            if not dev_found:
                raise Exception(f"Device '{device_id}' is not connected via ADB.")

            adb_service.reverse_port(device_id)

            # Bring Snapchat to foreground deterministically
            adb_service.launch_snapchat(device_id)
            await asyncio.sleep(1.2)

            adb_service.dismiss_heads_up_notification(device_id)
            adb_service.dismiss_popups(device_id)

            await self._step(
                f"Starting algorithmic Snapscore booster: {cycles} automated dispatch cycle(s)...",
                delay=1.0,
                reason="BOOSTER_START"
            )

            total_estimated_score = 0

            for cycle in range(1, cycles + 1):
                if state_machine.is_stopped:
                    raise Exception("Halted by Emergency STOP")

                await self._step(
                    f"[Cycle {cycle}/{cycles}] Capturing fresh Snap for score generation...",
                    delay=0.6
                )

                # Ensure camera landing
                adb_service.ensure_landing_or_search(device_id)

                # Check interruptions
                adb_service.dismiss_heads_up_notification(device_id)

                # 1. Capture Snap photo
                adb_service.capture_snap_photo(device_id)
                await asyncio.sleep(1.2)

                # 2. Apply random aesthetic filter
                swipes = random.randint(1, 3)
                adb_service.apply_random_filter(device_id, swipes_count=swipes)
                await asyncio.sleep(0.8)

                # 3. Open Send To screen
                adb_service.open_send_to_screen(device_id)
                await asyncio.sleep(1.2)

                # 4. Select recipients & send
                recipients_sent = adb_service.select_recipients_and_send(
                    device_id,
                    select_all=select_all,
                    max_recipients=max_recipients
                )
                cycle_score = max(1, recipients_sent)
                total_estimated_score += cycle_score

                await self._step(
                    f"[Cycle {cycle}/{cycles}] Snap delivered to {recipients_sent} contact(s). Estimated points gained: +{cycle_score} (Total: +{total_estimated_score}).",
                    delay=1.0,
                    reason="CYCLE_DISPATCH_COMPLETE"
                )

                # 5. Cooldown pause between cycles (anti-ban behavior)
                if cycle < cycles:
                    jitter_cooldown = cooldown_seconds + random.randint(-2, 3)
                    jitter_cooldown = max(8, jitter_cooldown)
                    await self._step(
                        f"Anti-ban safety cooldown: Waiting {jitter_cooldown}s before cycle {cycle + 1}...",
                        delay=jitter_cooldown,
                        reason="COOLDOWN_WAIT"
                    )

            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                await self._step(
                    f"Snapscore Booster completed! All {cycles} cycles executed. Estimated score increase: +{total_estimated_score} points.",
                    delay=0.5,
                    reason="BOOSTER_COMPLETE"
                )

            return {"status": "ok", "total_estimated_points": total_estimated_score}

        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                await self._step(
                    f"Snapscore booster halted: {str(e)}",
                    delay=0.5,
                    status=ResultStatus.FAILED,
                    reason="BOOSTER_FAILED"
                )
            return {"status": "error", "message": str(e)}
        finally:
            self._is_running = False

snapscore_engine = SnapscoreEngine()
