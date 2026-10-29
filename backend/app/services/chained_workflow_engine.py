import asyncio
import random
from typing import List, Dict, Any, Optional
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .adb_service import adb_service
from .bulk_follow_engine import bulk_follow_engine
from .bulk_unfollow_engine import bulk_unfollow_engine
from .auto_snap_engine import auto_snap_engine
from .snapscore_engine import snapscore_engine
from ..models.schemas import AppState, ResultStatus

class ChainedWorkflowEngine:
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
        reason: str = "CHAIN_STEP_OK"
    ):
        if state_machine.is_stopped:
            raise Exception("Chained workflow halted by user via Emergency STOP")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Chained workflow halted while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Chained Routine Engine",
            result=status,
            reason_code=reason,
            message=message
        )
        await ws_hub.broadcast_audit_log(entry)
        if delay > 0:
            await asyncio.sleep(delay)

    async def run_chained_routine(
        self,
        device_id: str,
        routine_type: str = "morning", # "morning" | "score_and_clean" | "all_in_one" | "custom"
        custom_steps: Optional[List[Dict[str, Any]]] = None
    ):
        if self._is_running:
            return {"status": "error", "message": "An automation workflow is already running"}

        self._is_running = True
        routine_names = {
            "morning": "Morning Growth Routine (Auto Snap + Quick Add)",
            "score_and_clean": "Score Booster & Unfollow Inactive Routine",
            "all_in_one": "All-in-One Daily Power Suite",
            "custom": "Custom Multi-Stage Sequence"
        }
        title = routine_names.get(routine_type, "Chained Automation Routine")
        state_machine.start_workflow(workflow=title)

        try:
            await self._step(f"Initiating '{title}'...", delay=1.0, reason="CHAIN_START")

            # Define sequence based on routine
            if routine_type == "morning":
                # Stage 1: Auto Snap
                await self._step("Stage 1/2: Executing Auto Snap Dispatch...", delay=0.8)
                await auto_snap_engine.run_snap_workflow(device_id, random_filter=True, select_all=True, is_chained=True)

                if state_machine.is_stopped:
                    raise Exception("Halted during Stage 1")

                # Inter-stage pause
                rest = round(random.uniform(4.0, 7.0), 1)
                await self._step(f"Inter-stage rest: Cooling down for {rest}s...", delay=rest)

                # Stage 2: Quick Add
                await self._step("Stage 2/2: Executing Quick Add Suggestions...", delay=0.8)
                await bulk_follow_engine.run_follow_workflow(device_id, mode="quick_add", max_count=5, is_chained=True)

            elif routine_type == "score_and_clean":
                # Stage 1: Snapscore Booster
                await self._step("Stage 1/2: Executing Snapscore Booster (3 Cycles)...", delay=0.8)
                await snapscore_engine.run_booster_workflow(device_id, cycles=3, select_all=True, cooldown_seconds=12, is_chained=True)

                if state_machine.is_stopped:
                    raise Exception("Halted during Stage 1")

                rest = round(random.uniform(5.0, 8.0), 1)
                await self._step(f"Inter-stage rest: Cooling down for {rest}s...", delay=rest)

                # Stage 2: Unfollow Friends without Streak
                await self._step("Stage 2/2: Executing Smart Unfollow (No Streak 🔥)...", delay=0.8)
                await bulk_unfollow_engine.run_unfollow_workflow(device_id, filter_type="no_streak", max_unfollow=5, is_chained=True)

            elif routine_type == "all_in_one":
                # Stage 1: Auto Snap
                await self._step("Stage 1/4: Auto Snap Dispatch...", delay=0.6)
                await auto_snap_engine.run_snap_workflow(device_id, random_filter=True, select_all=True)

                await asyncio.sleep(4.0)

                # Stage 2: Quick Add
                await self._step("Stage 2/4: Quick Add Suggestions...", delay=0.6)
                await bulk_follow_engine.run_follow_workflow(device_id, mode="quick_add", max_count=5)

                await asyncio.sleep(4.0)

                # Stage 3: Accept Incoming
                await self._step("Stage 3/4: Accept Incoming Requests...", delay=0.6)
                await bulk_follow_engine.run_follow_workflow(device_id, mode="accept", max_count=5, is_chained=True)

                await asyncio.sleep(4.0)

                # Stage 4: Smart Unfollow
                await self._step("Stage 4/4: Smart Unfollow (Inactive >17 Days)...", delay=0.6)
                await bulk_unfollow_engine.run_unfollow_workflow(device_id, filter_type="inactive", days_threshold=17, max_unfollow=5, is_chained=True)

            elif routine_type == "custom" and custom_steps:
                for idx, step in enumerate(custom_steps, 1):
                    if state_machine.is_stopped:
                        break
                    action = step.get("action")
                    await self._step(f"Custom Stage {idx}/{len(custom_steps)}: {action}...", delay=0.5)

                    if action == "snap":
                        await auto_snap_engine.run_snap_workflow(device_id, random_filter=step.get("random_filter", True), is_chained=True)
                    elif action == "follow":
                        await bulk_follow_engine.run_follow_workflow(device_id, mode=step.get("mode", "quick_add"), max_count=step.get("count", 5), is_chained=True)
                    elif action == "unfollow":
                        await bulk_unfollow_engine.run_unfollow_workflow(device_id, filter_type=step.get("filter_type", "no_streak"), max_unfollow=step.get("count", 5), is_chained=True)
                    elif action == "snapscore":
                        await snapscore_engine.run_booster_workflow(device_id, cycles=step.get("cycles", 2), is_chained=True)

                    await asyncio.sleep(3.0)

            if not state_machine.is_stopped:
                adb_service.ensure_camera_landing(device_id)
                state_machine.transition_to(AppState.COMPLETED, workflow=title)
                await self._step(f"Chained routine '{title}' finished completely!", delay=0.5, reason="CHAIN_COMPLETE")

        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                await self._step(f"Chained routine halted: {str(e)}", delay=0.5, status=ResultStatus.FAILED, reason="CHAIN_FAILED")
        finally:
            self._is_running = False

chained_engine = ChainedWorkflowEngine()
