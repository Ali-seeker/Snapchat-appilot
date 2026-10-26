import pytest
import uuid
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.schemas import AppState, ResultStatus, ContactCreate
from backend.app.services.state_machine import WorkflowStateMachine, StateMachineError
from backend.app.services.contact_service import ContactService
from backend.app.services.audit_logger import AuditLogger
from pathlib import Path
import tempfile

def test_state_machine_transitions():
    sm = WorkflowStateMachine()
    assert sm.current_state == AppState.IDLE

    # Valid transitions: IDLE -> READY -> REVIEWING -> RUNNING -> COMPLETED
    sm.transition_to(AppState.READY)
    assert sm.current_state == AppState.READY

    sm.transition_to(AppState.REVIEWING)
    assert sm.current_state == AppState.REVIEWING

    sm.transition_to(AppState.RUNNING)
    assert sm.current_state == AppState.RUNNING

    sm.transition_to(AppState.COMPLETED)
    assert sm.current_state == AppState.COMPLETED

def test_state_machine_invalid_transition():
    sm = WorkflowStateMachine()
    assert sm.current_state == AppState.IDLE
    # IDLE cannot directly jump to RUNNING without READY or REVIEWING
    with pytest.raises(StateMachineError):
        sm.transition_to(AppState.RUNNING)

def test_state_machine_emergency_stop():
    sm = WorkflowStateMachine()
    sm.transition_to(AppState.READY)
    sm.transition_to(AppState.RUNNING)
    assert sm.current_state == AppState.RUNNING

    # Emergency stop can happen anytime
    sm.request_stop("User invoked emergency stop")
    assert sm.current_state == AppState.STOPPED
    assert sm.is_stopped is True

def test_contact_service_normalization_and_duplicates():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test_contacts.json"
        svc = ContactService(file_path=test_file)
        svc.clear_contacts()

        # Add valid contact
        c1, err1 = svc.add_contact(ContactCreate(username="  JohnDoe123  ", display_name="John Doe"))
        assert err1 == ""
        assert c1 is not None
        assert c1.username == "johndoe123"  # Normalized to lowercase and trimmed

        # Try duplicate with different case and spaces
        c2, err2 = svc.add_contact(ContactCreate(username="JOHNDOE123", display_name="Duplicate John"))
        assert c2 is None
        assert "already exists" in err2

        # Invalid username (too short)
        c3, err3 = svc.add_contact(ContactCreate(username="ab", display_name="Too short"))
        assert c3 is None
        assert "at least 3 characters" in err3

        # Invalid characters
        c4, err4 = svc.add_contact(ContactCreate(username="invalid@user!", display_name="Special chars"))
        assert c4 is None
        assert "alphanumeric" in err4

def test_audit_logger_redaction():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "test_audit.json"
        logger = AuditLogger(log_path=test_file)
        entry = logger.log(
            workflow="Auth Test",
            result=ResultStatus.COMPLETED,
            reason_code="AUTH_CHECK",
            message="Testing redaction",
            details={"safe_param": "visible", "password": "SuperSecretPassword123", "session_token": "xyz789"}
        )
        assert entry.details["safe_param"] == "visible"
        assert entry.details["password"] == "[REDACTED]"
        assert entry.details["session_token"] == "[REDACTED]"

def test_api_status_and_contacts():
    client = TestClient(app)
    # Check status endpoint
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "state" in data
    assert "devices" in data

    # Check contacts list
    res = client.get("/api/contacts")
    assert res.status_code == 200
    contacts = res.json()
    assert isinstance(contacts, list)
    assert len(contacts) > 0  # Seeded with demo contacts

    # Post contact with unique username
    unique_name = f"bot_{uuid.uuid4().hex[:6]}"
    res = client.post("/api/contacts", json={"username": unique_name, "display_name": "New Tester"})
    assert res.status_code == 200
    new_c = res.json()
    assert new_c["username"] == unique_name

    # Emergency stop API
    res = client.post("/api/control/stop")
    assert res.status_code == 200
    assert res.json()["state"] == "STOPPED"
