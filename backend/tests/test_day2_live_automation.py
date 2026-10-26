import pytest
import asyncio
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.adb_service import adb_service
from backend.app.services.live_automation_engine import live_engine
from backend.app.services.state_machine import state_machine
from backend.app.services.contact_service import contact_service
from backend.app.models.schemas import AppState, ResultStatus, ContactCreate

client = TestClient(app)

def setup_function():
    state_machine.reset_to_idle()

def test_adb_service_capabilities():
    """Verify ADB Service exposes all required live automation primitives"""
    assert hasattr(adb_service, "launch_snapchat")
    assert hasattr(adb_service, "stop_snapchat")
    assert hasattr(adb_service, "input_tap")
    assert hasattr(adb_service, "input_text")
    assert hasattr(adb_service, "input_key")
    assert hasattr(adb_service, "dump_ui_hierarchy")
    assert hasattr(adb_service, "find_bounds")
    assert hasattr(adb_service, "take_screenshot")

def test_find_bounds_xml_parsing():
    """Verify ADB XML hierarchy bounds parser extracts center (x, y) coordinates"""
    sample_xml = '''<?xml version="1.0" encoding="utf-8"?>
    <hierarchy rotation="0">
        <node index="0" text="Search" resource-id="com.snapchat.android:id/search_bar" bounds="[100,50][300,150]" />
        <node index="1" text="Add" resource-id="com.snapchat.android:id/add_button" bounds="[800,200][900,260]" />
    </hierarchy>'''

    with patch.object(adb_service, "dump_ui_hierarchy", return_value=sample_xml):
        search_coords = adb_service.find_bounds("dummy_device", "search")
        assert search_coords == (200, 100) # center of [100,50][300,150]

        add_coords = adb_service.find_bounds("dummy_device", "add")
        assert add_coords == (850, 230) # center of [800,200][900,260]

        missing = adb_service.find_bounds("dummy_device", "nonexistent_element")
        assert missing is None

def test_live_automation_flow_execution():
    """Verify LiveAutomationEngine executes live flow with ADB primitives and state machine updates"""
    async def _test():
        unique_name = f"user_{uuid.uuid4().hex[:8]}"
        target, _ = contact_service.add_contact(ContactCreate(username=unique_name, display_name="Live Tester"))
        assert target is not None

        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="test_phone")]), \
             patch.object(adb_service, "launch_snapchat", return_value=True), \
             patch.object(adb_service, "find_bounds", return_value=(200, 100)), \
             patch.object(adb_service, "input_tap", return_value=True), \
             patch.object(adb_service, "input_text", return_value=True), \
             patch.object(adb_service, "input_key", return_value=True):

            # Run with short delay for test
            with patch("asyncio.sleep", return_value=None):
                await live_engine.run_live_add_workflow("test_phone", target_ids=[target.id])

            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]
            assert not live_engine.is_running

    asyncio.run(_test())

def test_live_automation_emergency_stop():
    """Verify LiveAutomationEngine halts immediately when Emergency STOP is triggered"""
    async def _test():
        unique_name = f"stop_{uuid.uuid4().hex[:8]}"
        target, _ = contact_service.add_contact(ContactCreate(username=unique_name, display_name="Stop Tester"))
        assert target is not None

        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="test_phone")]), \
             patch.object(adb_service, "launch_snapchat", return_value=True):

            # Trigger emergency stop before second step
            def mock_step_effect(*args, **kwargs):
                state_machine.request_stop("Emergency Stop in test")

            with patch.object(live_engine, "_step", side_effect=mock_step_effect):
                await live_engine.run_live_add_workflow("test_phone", target_ids=[target.id])

            assert state_machine.is_stopped is True
            assert state_machine.current_state == AppState.STOPPED

    asyncio.run(_test())

def test_live_api_endpoint():
    """Verify POST /api/live/run accepts request and launches live automation task"""
    res = client.post("/api/live/run", json={"target_ids": [], "action": "add"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "started"
    assert "device_id" in data
