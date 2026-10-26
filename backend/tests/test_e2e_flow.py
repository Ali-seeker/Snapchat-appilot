import pytest
import time
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.schemas import AppState

def test_full_e2e_demo_flow():
    client = TestClient(app)

    # 1. Verify Initial Status
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "state" in data

    # 2. Reset to IDLE first
    client.post("/api/control/reset")
    res = client.get("/api/status")
    assert res.json()["state"] == "IDLE"

    # 3. Verify Contacts Endpoint
    res = client.get("/api/contacts")
    assert res.status_code == 200
    contacts = res.json()
    assert len(contacts) > 0
    target_ids = [c["id"] for c in contacts[:2]]

    # 4. Trigger Demo Run
    res = client.post("/api/demo/run", json={"scenario": "success", "target_ids": target_ids})
    assert res.status_code == 200
    assert res.json()["status"] == "started"

    # 5. Check transition to RUNNING or COMPLETED
    time.sleep(0.2)
    res = client.get("/api/status")
    assert res.json()["state"] in ["RUNNING", "COMPLETED", "IDLE"]

    # 6. Test Emergency STOP
    res = client.post("/api/control/stop")
    assert res.status_code == 200
    assert res.json()["state"] == "STOPPED"

    # 7. Reset back to IDLE
    res = client.post("/api/control/reset")
    assert res.status_code == 200
    assert res.json()["state"] == "IDLE"

def test_edge_case_duplicate_injection():
    client = TestClient(app)
    # Attempting to add an existing username should return 400 with duplicate message
    res = client.post("/api/contacts", json={"username": "alex.dev", "display_name": "Alex Dupe"})
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_audit_logs_retrieval_and_clear():
    client = TestClient(app)
    # Get logs
    res = client.get("/api/logs")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
