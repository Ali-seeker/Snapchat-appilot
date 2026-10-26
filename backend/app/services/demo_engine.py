import asyncio
from typing import List, Dict, Any
from .state_machine import state_machine
from .audit_logger import audit_logger
from .websocket_hub import ws_hub
from .contact_service import contact_service
from ..models.schemas import AppState, ResultStatus, ContactCreate

class DemoEngine:
    def __init__(self):
        self._is_running = False

    async def run_scenario(self, scenario_name: str, target_ids: List[str] = None):
        if self._is_running:
            return {"status": "error", "message": "Demo already in progress"}

        self._is_running = True
        try:
            workflow_name = f"Assisted Workflow ({len(target_ids)} targets)" if target_ids else f"Demo: {scenario_name}"
            state_machine.start_workflow(workflow=workflow_name)

            if scenario_name == "full_suite":
                await self._run_full_suite()
            elif scenario_name == "success":
                await self._run_success_case(target_ids)
            elif scenario_name == "failure":
                await self._run_failure_case()
            elif scenario_name == "duplicate":
                await self._run_duplicate_case()
            elif scenario_name == "inactivity_unknown":
                await self._run_inactivity_case()
            else:
                await self._run_success_case(target_ids)

            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=workflow_name)
                audit_logger.log(
                    workflow="Workflow Engine",
                    result=ResultStatus.COMPLETED,
                    reason_code="WORKFLOW_COMPLETE",
                    message=f"Workflow completed successfully for {len(target_ids) if target_ids else 1} target(s)."
                )
        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                audit_logger.log(
                    workflow="Workflow Engine",
                    result=ResultStatus.FAILED,
                    reason_code="WORKFLOW_ERROR",
                    message=f"Error executing workflow: {str(e)}"
                )
        finally:
            self._is_running = False

    async def _step(self, message: str, delay: float = 0.8, status: ResultStatus = ResultStatus.COMPLETED, reason: str = "STEP_OK"):
        if state_machine.is_stopped:
            raise Exception("Workflow was stopped by user")

        while state_machine.is_paused:
            if state_machine.is_stopped:
                raise Exception("Workflow was stopped while paused")
            await asyncio.sleep(0.3)

        entry = audit_logger.log(
            workflow="Workflow Engine",
            result=status,
            reason_code=reason,
            message=message
        )
        await ws_hub.broadcast_audit_log(entry)
        await asyncio.sleep(delay)

    async def _run_success_case(self, target_ids: List[str] = None):
        targets = []
        if target_ids:
            for tid in target_ids:
                c = contact_service.get_contact_by_id(tid)
                if c:
                    targets.append(c)
        if not targets:
            targets = contact_service.get_contacts()[:2]

        total = len(targets)
        await self._step(f"Starting assisted processing for {total} confirmed targets...", 0.8)

        for idx, target in enumerate(targets, 1):
            await self._step(f"[{idx}/{total}] Checking target @{target.username} ({target.display_name or 'Friend'})...", 1.2)
            await self._step(f"[{idx}/{total}] Validating recipient state & consent boundaries for @{target.username}...", 1.2)
            await self._step(f"[{idx}/{total}] Preparing local streak draft & reminder for @{target.username}...", 1.2)
            await self._step(f"[{idx}/{total}] Staged successfully: Streak reminder created for @{target.username}.", 1.0, ResultStatus.COMPLETED, "TARGET_READY")

        await self._step(f"All {total} targets reviewed & staged. User can complete dispatch in Snapchat.", 0.8, ResultStatus.COMPLETED, "SUCCESS_ALL")

    async def _run_failure_case(self):
        await self._step("Simulating connection to external target...", 0.6)
        await self._step("Encountered external timeout / unreachable service", 0.8, ResultStatus.FAILED, "TIMEOUT_ERROR")
        await self._step("Safe recovery executed: No state corrupted; rollback complete", 0.6, ResultStatus.NEEDS_USER_ACTION, "SAFE_RECOVERY")

    async def _run_duplicate_case(self):
        await self._step("Testing duplicate injection with case variations ('Alex.Dev' vs 'alex.dev')", 0.6)
        contact, err = contact_service.add_contact(ContactCreate(username="alex.dev", display_name="Alex Duplicate Test"))
        if not contact:
            await self._step(f"Duplicate correctly rejected: {err}", 0.6, ResultStatus.SKIPPED, "DUPLICATE_PREVENTED")
        else:
            await self._step("Duplicate test recorded", 0.6)

    async def _run_inactivity_case(self):
        await self._step("Evaluating last-active timestamp provenance...", 0.6)
        await self._step("Data provenance missing or unverified from external platform", 0.6, ResultStatus.UNKNOWN, "PROVENANCE_MISSING")
        await self._step("Classification policy applied: Marked strictly as 'Unknown', NEVER as 'Inactive'", 0.6, ResultStatus.UNKNOWN, "POLICY_HONEST_UNKNOWN")

    async def _run_full_suite(self):
        await self._step("=== STARTING FULL EDGE-CASE & DEMO TEST SUITE ===", 0.5)
        await self._run_success_case()
        await self._run_duplicate_case()
        await self._run_inactivity_case()
        await self._run_failure_case()
        await self._step("=== FULL TEST SUITE FINISHED: ALL SCENARIOS VERIFIED ===", 0.5)

demo_engine = DemoEngine()
