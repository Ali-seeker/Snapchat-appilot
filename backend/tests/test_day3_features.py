import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import AppState, ResultStatus
from backend.app.services.state_machine import state_machine
from backend.app.services.adb_service import adb_service
from backend.app.services.bulk_follow_engine import bulk_follow_engine
from backend.app.services.bulk_unfollow_engine import bulk_unfollow_engine
from backend.app.services.auto_snap_engine import auto_snap_engine
from backend.app.services.snapscore_engine import snapscore_engine
from backend.app.services.chained_workflow_engine import chained_engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_state():
    state_machine.reset_to_idle()
    yield
    state_machine.reset_to_idle()

def test_bulk_follow_quick_add():
    """Verify BulkFollowEngine executes Quick Add suggestions flow"""
    async def _test():
        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="dev1")]), \
             patch.object(adb_service, "reverse_port", return_value=True), \
             patch.object(adb_service, "dismiss_heads_up_notification", return_value=True), \
             patch.object(adb_service, "dismiss_popups", return_value=True), \
             patch.object(adb_service, "ensure_landing_or_search", return_value=True), \
             patch.object(adb_service, "open_add_friends_page", return_value=True), \
             patch.object(adb_service, "quick_add_batch", return_value=3), \
             patch.object(adb_service, "scroll_down", return_value=True), \
             patch.object(adb_service, "input_key", return_value=True), \
             patch("asyncio.sleep", return_value=None), \
             patch("time.sleep", return_value=None):

            await bulk_follow_engine.run_follow_workflow("dev1", mode="quick_add", max_count=3)

            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]
            assert not bulk_follow_engine.is_running

    asyncio.run(_test())

def test_bulk_follow_accept():
    """Verify BulkFollowEngine accepts incoming requests under 'Added Me'"""
    async def _test():
        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="dev1")]), \
             patch.object(adb_service, "reverse_port", return_value=True), \
             patch.object(adb_service, "dismiss_heads_up_notification", return_value=True), \
             patch.object(adb_service, "dismiss_popups", return_value=True), \
             patch.object(adb_service, "ensure_landing_or_search", return_value=True), \
             patch.object(adb_service, "open_add_friends_page", return_value=True), \
             patch.object(adb_service, "accept_incoming_requests", return_value=2), \
             patch.object(adb_service, "input_key", return_value=True), \
             patch("asyncio.sleep", return_value=None), \
             patch("time.sleep", return_value=None):

            await bulk_follow_engine.run_follow_workflow("dev1", mode="accept", max_count=5)

            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]
            assert not bulk_follow_engine.is_running

    asyncio.run(_test())

def test_bulk_unfollow_no_streak():
    """Verify BulkUnfollowEngine removes friends without active streak"""
    async def _test():
        mock_candidates = [
            {"name": "DormantUser1", "center": (360, 400), "bounds": (0, 350, 720, 450), "reason": "No active streak emoji (🔥) found"}
        ]
        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="dev1")]), \
             patch.object(adb_service, "reverse_port", return_value=True), \
             patch.object(adb_service, "dismiss_heads_up_notification", return_value=True), \
             patch.object(adb_service, "dismiss_popups", return_value=True), \
             patch.object(adb_service, "ensure_landing_or_search", return_value=True), \
             patch.object(adb_service, "open_chat_screen", return_value=True), \
             patch.object(adb_service, "scan_chat_friends_and_filter", return_value=mock_candidates), \
             patch.object(adb_service, "unfollow_friend", return_value=True), \
             patch.object(adb_service, "input_key", return_value=True), \
             patch("asyncio.sleep", return_value=None), \
             patch("time.sleep", return_value=None):

            await bulk_unfollow_engine.run_unfollow_workflow("dev1", filter_type="no_streak", max_unfollow=1)

            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]
            assert not bulk_unfollow_engine.is_running

    asyncio.run(_test())

def test_auto_snap_workflow():
    """Verify AutoSnapEngine captures photo, applies random filter, and sends to recipients"""
    async def _test():
        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="dev1")]), \
             patch.object(adb_service, "reverse_port", return_value=True), \
             patch.object(adb_service, "dismiss_heads_up_notification", return_value=True), \
             patch.object(adb_service, "dismiss_popups", return_value=True), \
             patch.object(adb_service, "ensure_landing_or_search", return_value=True), \
             patch.object(adb_service, "capture_snap_photo", return_value=True), \
             patch.object(adb_service, "apply_random_filter", return_value=True), \
             patch.object(adb_service, "open_send_to_screen", return_value=True), \
             patch.object(adb_service, "select_recipients_and_send", return_value=5), \
             patch("asyncio.sleep", return_value=None), \
             patch("time.sleep", return_value=None):

            res = await auto_snap_engine.run_snap_workflow("dev1", random_filter=True, select_all=True)

            assert res["status"] == "ok"
            assert res["recipients_count"] == 5
            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]

    asyncio.run(_test())

def test_snapscore_booster():
    """Verify SnapscoreEngine runs multi-cycle dispatch and estimates score increase"""
    async def _test():
        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="dev1")]), \
             patch.object(adb_service, "reverse_port", return_value=True), \
             patch.object(adb_service, "dismiss_heads_up_notification", return_value=True), \
             patch.object(adb_service, "dismiss_popups", return_value=True), \
             patch.object(adb_service, "ensure_landing_or_search", return_value=True), \
             patch.object(adb_service, "capture_snap_photo", return_value=True), \
             patch.object(adb_service, "apply_random_filter", return_value=True), \
             patch.object(adb_service, "open_send_to_screen", return_value=True), \
             patch.object(adb_service, "select_recipients_and_send", return_value=10), \
             patch("asyncio.sleep", return_value=None), \
             patch("time.sleep", return_value=None):

            res = await snapscore_engine.run_booster_workflow("dev1", cycles=2, cooldown_seconds=0)

            assert res["status"] == "ok"
            assert res["total_estimated_points"] == 20
            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]

    asyncio.run(_test())

def test_chained_morning_routine():
    """Verify ChainedWorkflowEngine executes sequential multi-stage automation"""
    async def _test():
        with patch.object(auto_snap_engine, "run_snap_workflow", return_value={"status": "ok"}), \
             patch.object(bulk_follow_engine, "run_follow_workflow", return_value={"status": "ok"}), \
             patch("asyncio.sleep", return_value=None):

            await chained_engine.run_chained_routine("dev1", routine_type="morning")

            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]
            assert not chained_engine.is_running

    asyncio.run(_test())

def test_api_workflow_endpoints():
    """Verify all 5 Day 3 REST endpoints respond correctly"""
    # Follow
    res = client.post("/api/workflow/follow", json={"mode": "quick_add", "max_count": 5})
    assert res.status_code == 200
    assert res.json()["status"] == "started"

    # Unfollow
    res = client.post("/api/workflow/unfollow", json={"filter_type": "no_streak", "max_unfollow": 5})
    assert res.status_code == 200
    assert res.json()["status"] == "started"

    # Snap
    res = client.post("/api/workflow/snap", json={"random_filter": True, "select_all": True})
    assert res.status_code == 200
    assert res.json()["status"] == "started"

    # Snapscore
    res = client.post("/api/workflow/snapscore", json={"cycles": 3, "select_all": True})
    assert res.status_code == 200
    assert res.json()["status"] == "started"

    # Chain
    res = client.post("/api/workflow/chain", json={"routine_type": "morning"})
    assert res.status_code == 200
    assert res.json()["status"] == "started"
