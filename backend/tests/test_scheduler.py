import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from backend.app.services.scheduler_service import (
    SchedulerService, ScheduleCreate, ScheduleItem
)
from backend.app.services.adb_service import adb_service
from backend.app.services.state_machine import state_machine, AppState
from backend.app.models.schemas import DeviceInfo


@pytest.fixture
def tmp_scheduler(tmp_path):
    p = tmp_path / "test_schedules.json"
    service = SchedulerService(data_path=p)
    return service


def test_scheduler_crud(tmp_scheduler):
    # 1. Create schedule
    new_item = tmp_scheduler.create(ScheduleCreate(
        title="Late Night Score Run",
        automation_type="snapscore",
        params={"cycles": 5, "recipient_mode": "shortcut", "shortcut_emoji": "🤙"},
        date="2026-10-30",
        start_time="23:30",
        end_time="01:00",
        frequency="daily"
    ))
    assert new_item.id is not None
    assert new_item.title == "Late Night Score Run"
    assert new_item.is_active is True

    # 2. Get list & by ID
    all_items = tmp_scheduler.get_all()
    assert any(s.id == new_item.id for s in all_items)
    fetched = tmp_scheduler.get_by_id(new_item.id)
    assert fetched is not None
    assert fetched.params["cycles"] == 5

    # 3. Toggle active
    toggled = tmp_scheduler.toggle(new_item.id)
    assert toggled.is_active is False
    toggled_again = tmp_scheduler.toggle(new_item.id)
    assert toggled_again.is_active is True

    # 4. Update
    updated = tmp_scheduler.update(new_item.id, {"title": "Updated Title"})
    assert updated.title == "Updated Title"

    # 5. Delete
    deleted = tmp_scheduler.delete(new_item.id)
    assert deleted is True
    assert tmp_scheduler.get_by_id(new_item.id) is None


def test_scheduler_device_offline_handling(tmp_scheduler):
    """
    CRITICAL EDGE CASE: When scheduled time arrives but target phone is disconnected.
    System must not crash, must cleanly mark schedule as DEVICE_OFFLINE and log warning.
    """
    async def _test():
        sched = tmp_scheduler.create(ScheduleCreate(
            title="Morning Run",
            automation_type="snapscore",
            params={"cycles": 2},
            date="2026-10-29",
            start_time="10:00",
            frequency="once"
        ))

        # Mock ADB returning NO devices connected (phone unplugged)
        with patch.object(adb_service, "list_devices", return_value=[]):
            res = await tmp_scheduler.execute_schedule(sched)
            assert res["status"] == "error"
            assert res["reason"] == "DEVICE_OFFLINE"

            # Verify schedule record has updated error status without breaking
            assert sched.last_status == "DEVICE_OFFLINE"
            assert "not connected" in sched.last_error.lower()

    asyncio.run(_test())


def test_scheduler_device_online_execution(tmp_scheduler):
    """
    Verify full execution when device is connected: runs engine, marks COMPLETED,
    and advances date for recurring daily schedule.
    """
    async def _test():
        sched = tmp_scheduler.create(ScheduleCreate(
            title="Daily Score Booster",
            automation_type="snapscore",
            params={"cycles": 3, "recipient_mode": "count"},
            date="2026-10-29",
            start_time="14:00",
            frequency="daily"
        ))

        mock_dev = DeviceInfo(device_id="dev_123", is_connected=True)

        with patch.object(adb_service, "list_devices", return_value=[mock_dev]), \
             patch("backend.app.services.scheduler_service.snapscore_engine.run_booster_workflow", return_value={"status": "ok"}), \
             patch("backend.app.services.websocket_hub.ws_hub.broadcast_audit_log", return_value=None):

            res = await tmp_scheduler.execute_schedule(sched)
            assert res["status"] == "ok"
            assert sched.last_status == "PENDING"  # Advanced to tomorrow and pending
            assert sched.date == "2026-10-30"  # Advanced to next day!

    asyncio.run(_test())

