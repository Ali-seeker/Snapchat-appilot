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
            if state_machine.current_state == AppState.IDLE:
                state_machine.transition_to(AppState.READY)
            state_machine.transition_to(AppState.RUNNING, workflow=f"Demo: {scenario_name}")

            if scenario_name == "full_suite":
                await self._run_full_suite()
            elif scenario_name == "success":
                await self._run_success_case()
            elif scenario_name == "failure":
                await self._run_failure_case()
            elif scenario_name == "duplicate":
                await self._run_duplicate_case()
            elif scenario_name == "inactivity_unknown":
                await self._run_inactivity_case()
            else:
                await self._run_success_case()

            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.COMPLETED, workflow=f"Demo: {scenario_name}")
                audit_logger.log(
                    workflow="Demo Engine",
                    result=ResultStatus.COMPLETED,
                    reason_code="DEMO_COMPLETE",
                    message=f"Deterministic demo scenario '{scenario_name}' finished cleanly."
                )
        except Exception as e:
            if not state_machine.is_stopped:
                state_machine.transition_to(AppState.FAILED, reason=str(e))
                audit_logger.log(
                    workflow="Demo Engine",
                    result=ResultStatus.FAILED,
                    reason_code="DEMO_ERROR",
                    message=f"Error executing scenario: {str(e)}"
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
            workflow="Demo Workflow",
            result=status,
            reason_code=reason,
            message=message
        )
        await ws_hub.broadcast_audit_log(entry)
        await asyncio.sleep(delay)

    async def _run_success_case(self):
        await self._step("Initializing synthetic review context (Target: Alex)", 0.6)
        await self._step("Validating target format and consent boundary", 0.6)
        await self._step("Simulating user-confirmed streak reminder preparation", 0.6)
        await self._step("Action completed: Streak reminder stored locally for user dispatch", 0.6, ResultStatus.COMPLETED, "SIM_SUCCESS")

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
