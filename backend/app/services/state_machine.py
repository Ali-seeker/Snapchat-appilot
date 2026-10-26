import asyncio
from typing import Callable, List, Optional
from ..models.schemas import AppState, ResultStatus
from .audit_logger import audit_logger

class StateMachineError(Exception):
    pass

class WorkflowStateMachine:
    def __init__(self):
        self._current_state: AppState = AppState.IDLE
        self._current_workflow: Optional[str] = None
        self._listeners: List[Callable[[AppState, Optional[str]], None]] = []
        self._stop_requested: bool = False
        self._pause_requested: bool = False

    @property
    def current_state(self) -> AppState:
        return self._current_state

    @property
    def current_workflow(self) -> Optional[str]:
        return self._current_workflow

    @property
    def is_stopped(self) -> bool:
        return self._stop_requested

    @property
    def is_paused(self) -> bool:
        return self._pause_requested

    def register_listener(self, callback: Callable[[AppState, Optional[str]], None]):
        self._listeners.append(callback)

    def _notify(self):
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    asyncio.create_task(listener(self._current_state, self._current_workflow))
                else:
                    listener(self._current_state, self._current_workflow)
            except Exception:
                pass

    def transition_to(self, new_state: AppState, workflow: Optional[str] = None, reason: str = "") -> bool:
        allowed_transitions = {
            AppState.IDLE: [AppState.READY, AppState.REVIEWING, AppState.FAILED],
            AppState.READY: [AppState.REVIEWING, AppState.IDLE, AppState.RUNNING, AppState.FAILED],
            AppState.REVIEWING: [AppState.READY, AppState.RUNNING, AppState.IDLE, AppState.STOPPED],
            AppState.RUNNING: [AppState.PAUSED, AppState.STOPPED, AppState.COMPLETED, AppState.FAILED, AppState.NEEDS_USER_ACTION],
            AppState.PAUSED: [AppState.RUNNING, AppState.STOPPED, AppState.FAILED],
            AppState.STOPPED: [AppState.IDLE, AppState.READY],
            AppState.COMPLETED: [AppState.IDLE, AppState.READY],
            AppState.FAILED: [AppState.IDLE, AppState.READY],
            AppState.NEEDS_USER_ACTION: [AppState.RUNNING, AppState.STOPPED, AppState.FAILED]
        }

        # Any state can transition to STOPPED if emergency stop is triggered
        if new_state == AppState.STOPPED:
            self._current_state = AppState.STOPPED
            self._stop_requested = True
            self._pause_requested = False
            audit_logger.log(
                workflow=workflow or self._current_workflow or "System",
                result=ResultStatus.CANCELLED,
                reason_code="USER_EMERGENCY_STOP",
                message=f"Emergency stop executed: {reason or 'User requested stop'}"
            )
            self._notify()
            return True

        if new_state not in allowed_transitions.get(self._current_state, []):
            raise StateMachineError(
                f"Invalid state transition from {self._current_state} to {new_state}"
            )

        old_state = self._current_state
        self._current_state = new_state
        if workflow:
            self._current_workflow = workflow

        if new_state == AppState.RUNNING:
            self._stop_requested = False
            self._pause_requested = False

        self._notify()
        return True

    def request_stop(self, reason: str = "User pressed Emergency STOP") -> bool:
        self._stop_requested = True
        self.transition_to(AppState.STOPPED, reason=reason)
        return True

    def request_pause(self) -> bool:
        if self._current_state == AppState.RUNNING:
            self._pause_requested = True
            self.transition_to(AppState.PAUSED, reason="User paused execution")
            audit_logger.log(
                workflow=self._current_workflow or "General",
                result=ResultStatus.SKIPPED,
                reason_code="USER_PAUSE",
                message="Workflow paused by user"
            )
            return True
        return False

    def request_resume(self) -> bool:
        if self._current_state == AppState.PAUSED:
            self._pause_requested = False
            self.transition_to(AppState.RUNNING, reason="User resumed execution")
            return True
        return False

    def reset_to_idle(self):
        self._stop_requested = False
        self._pause_requested = False
        self._current_workflow = None
        self._current_state = AppState.IDLE
        self._notify()

state_machine = WorkflowStateMachine()
