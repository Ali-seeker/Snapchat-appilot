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

def test_send_to_recipient_boundary_isolation():
    """Verify select_recipients_and_send strictly isolates Best Friends and Recents, never clicking Find Friends"""
    import os
    send_to_path = os.path.join(os.path.dirname(__file__), "..", "..", "send_to_dump.xml")
    if not os.path.exists(send_to_path):
        return

    with open(send_to_path, "r", encoding="utf-8", errors="ignore") as f:
        xml_initial = f.read()

    xml_with_send_btn = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
    <hierarchy rotation="0">
        <node index="0" text="" class="android.widget.FrameLayout" bounds="[0,0][720,1600]">
            <node index="0" text="" resource-id="com.snapchat.android:id/send_to_confirmation_bar" bounds="[0,1511][720,1567]">
                <node index="0" text="" resource-id="com.snapchat.android:id/send_to_send_button" content-desc="Send" bounds="[623,1540][704,1567]" />
            </node>
        </node>
    </hierarchy>"""

    taps = []
    def mock_tap(device_id, x, y, bounds=None):
        taps.append((x, y))

    stream = [xml_initial]
    def mock_dump(dev):
        return stream.pop(0) if stream else xml_with_send_btn

    with patch.object(adb_service, "dismiss_popups", return_value=True), \
         patch.object(adb_service, "dump_ui_hierarchy", side_effect=mock_dump), \
         patch.object(adb_service, "input_tap_human", side_effect=mock_tap), \
         patch("time.sleep", return_value=None):

        count = adb_service.select_recipients_and_send("dev1", select_all=False, max_recipients=1)
        assert count >= 1

    # Verify recipient selection tap
    recipient_tap = taps[0]
    assert recipient_tap[0] == 633, "Recipient checkbox X coordinate should be 633"
    assert 700 <= recipient_tap[1] < 1528, f"Recipient tap Y coordinate {recipient_tap[1]} must be above Find Friends (1528)"

def test_ensure_landing_from_chat_feed():
    """Verify ensure_landing_or_search detects CHAT_FEED and safely returns to CAMERA_LANDING"""
    states = ["CHAT_FEED", "CAMERA_LANDING"]
    def mock_detect(dev):
        return states.pop(0) if states else "CAMERA_LANDING"

    taps = []
    def mock_tap(dev, x, y):
        taps.append((x, y))

    with patch.object(adb_service, "is_snapchat_foreground", return_value=True), \
         patch.object(adb_service, "detect_screen_state", side_effect=mock_detect), \
         patch.object(adb_service, "find_element", return_value={"center": (359, 1541), "bounds": [294, 1515, 425, 1567]}), \
         patch.object(adb_service, "input_tap", side_effect=mock_tap), \
         patch("time.sleep", return_value=None):

        res = adb_service.ensure_landing_or_search("dev1")
        assert res is True
        assert (359, 1541) in taps



def test_shortcuts_crud_api():
    """Verify Snapchat Shortcuts CRUD operations via API"""
    client = TestClient(app)
    # 1. List
    res = client.get("/api/shortcuts")
    assert res.status_code == 200
    shortcuts = res.json()
    assert isinstance(shortcuts, list)

    # 2. Create
    create_res = client.post("/api/shortcuts", json={"name": "Streaks Squad", "emoji": "🔥"})
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["name"] == "Streaks Squad"
    assert created["emoji"] == "🔥"
    shortcut_id = created["id"]

    # 3. Verify in list
    res2 = client.get("/api/shortcuts")
    assert any(s["id"] == shortcut_id for s in res2.json())

    # 4. Delete
    del_res = client.delete(f"/api/shortcuts/{shortcut_id}")
    assert del_res.status_code == 200

    # 5. Verify deleted
    res3 = client.get("/api/shortcuts")
    assert not any(s["id"] == shortcut_id for s in res3.json())

def test_select_shortcut_and_send():
    """Verify select_shortcut_and_send locates shortcut tab by emoji and taps Select All"""
    sample_xml_send_to = """<hierarchy>
        <node bounds="[140,217][175,255]" text="🤙🏻" content-desc="🤙🏻" />
        <node bounds="[231,217][394,255]" text="New Friends" content-desc="New Friends" />
    </hierarchy>"""

    sample_xml_shortcut = """<hierarchy>
        <node bounds="[509,494][688,552]" text="" content-desc="Select All Button" />
        <node bounds="[148,612][520,656]" text="Nomi Ge" />
    </hierarchy>"""

    taps = []
    def mock_tap_human(dev, x, y, bounds=None):
        taps.append((x, y))

    xmls = [sample_xml_send_to, sample_xml_shortcut]
    def mock_dump(dev):
        return xmls.pop(0) if xmls else sample_xml_shortcut

    with patch.object(adb_service, "dismiss_popups", return_value=True), \
         patch.object(adb_service, "dump_ui_hierarchy", side_effect=mock_dump), \
         patch.object(adb_service, "input_tap_human", side_effect=mock_tap_human), \
         patch.object(adb_service, "detect_screen_state", return_value="CAMERA_LANDING"), \
         patch("time.sleep", return_value=None):

        res = adb_service.select_shortcut_and_send("dev1", "🤙")
        assert res == 1
        # First tap on shortcut tab
        assert taps[0] == (157, 236)
        # Second tap on Select All Button
        assert taps[1] == (598, 523)

def test_select_all_and_send():
    """Verify select_all_and_send locates global Select All Button and taps it"""
    sample_xml = """<hierarchy>
        <node bounds="[509,684][688,742]" text="" content-desc="Select All Button" />
        <node bounds="[32,684][213,728]" text="Best Friends" />
    </hierarchy>"""

    taps = []
    def mock_tap_human(dev, x, y, bounds=None):
        taps.append((x, y))

    with patch.object(adb_service, "dismiss_popups", return_value=True), \
         patch.object(adb_service, "dump_ui_hierarchy", return_value=sample_xml), \
         patch.object(adb_service, "input_tap_human", side_effect=mock_tap_human), \
         patch.object(adb_service, "detect_screen_state", return_value="CAMERA_LANDING"), \
         patch("time.sleep", return_value=None):

        res = adb_service.select_all_and_send("dev1")
        assert res == 1
        assert taps[0] == (598, 713)


def test_streak_friends_prioritization():
    """Verify select_recipients_and_send strictly isolates and prioritizes friends with active 🔥 streaks"""
    sample_xml = """<hierarchy>
        <node bounds="[32,684][213,728]" text="Best Friends" />
        <node bounds="[506,811][580,851]" text="3🔥😊" />
        <node bounds="[148,790][490,834]" text="Mr•Jalil" />
        <node bounds="[148,916][490,960]" text="NonStreakUser" />
        <node bounds="[536,1240][580,1280]" text="1🔥" />
        <node bounds="[148,1238][520,1282]" text="Sebiii" />
        <node bounds="[32,1528][250,1570]" text="Find Friends" />
        <node bounds="[623,1540][704,1567]" resource-id="com.snapchat.android:id/send_to_send_button" content-desc="Send" />
    </hierarchy>"""

    taps = []
    def mock_tap_human(dev, x, y, bounds=None):
        taps.append((x, y))

    with patch.object(adb_service, "dismiss_popups", return_value=True), \
         patch.object(adb_service, "dump_ui_hierarchy", return_value=sample_xml), \
         patch.object(adb_service, "input_tap_human", side_effect=mock_tap_human), \
         patch.object(adb_service, "detect_screen_state", return_value="CAMERA_LANDING"), \
         patch("time.sleep", return_value=None):

        count = adb_service.select_recipients_and_send("dev1", recipient_mode="count", max_recipients=5)
        # Should select both streak friends: Mr•Jalil (y=812) and Sebiii (y=1260)
        assert count == 2
        # Tap coordinates should match checkboxes of streak friends
        assert (633, 812) in taps
        assert (633, 1260) in taps
        # Non-streak user (y=938) must NOT be tapped
        assert (633, 938) not in taps


def test_select_shortcut_missing_emoji_fallback():
    """Verify select_shortcut_and_send gracefully falls back to Streak Friends if emoji is not on phone"""
    sample_xml_send_to = """<hierarchy>
        <node bounds="[48,217][84,255]" text="All" />
        <node bounds="[140,217][175,255]" text="🤙" />
        <node bounds="[32,684][213,728]" text="Best Friends" />
        <node bounds="[506,811][580,851]" text="3🔥😊" />
        <node bounds="[148,790][490,834]" text="Mr•Jalil" />
        <node bounds="[623,1540][704,1567]" resource-id="com.snapchat.android:id/send_to_send_button" content-desc="Send" />
    </hierarchy>"""

    taps = []
    def mock_tap_human(dev, x, y, bounds=None):
        taps.append((x, y))

    with patch.object(adb_service, "dismiss_popups", return_value=True), \
         patch.object(adb_service, "dump_ui_hierarchy", return_value=sample_xml_send_to), \
         patch.object(adb_service, "input_tap_human", side_effect=mock_tap_human), \
         patch.object(adb_service, "_run_cmd", return_value=""), \
         patch.object(adb_service, "detect_screen_state", return_value="CAMERA_LANDING"), \
         patch("time.sleep", return_value=None):

        # Pass a non-existent emoji: 🚀
        res = adb_service.select_shortcut_and_send("dev1", "🚀")
        # Should gracefully fall back to sending to streak friends
        assert res >= 1
        # Should have tapped Mr•Jalil (633, 812)
        assert (633, 812) in taps


def test_bulk_unfollow_select_all():
    """Verify BulkUnfollowEngine handles select_all=True (removing all non-streak contacts)"""
    async def _test():
        mock_candidates = [
            {"name": f"User_{i}", "center": (360, 400), "bounds": (0, 350, 720, 450), "reason": "No active streak emoji (🔥) found"}
            for i in range(3)
        ]
        with patch.object(adb_service, "list_devices", return_value=[MagicMock(device_id="dev1")]), \
             patch.object(adb_service, "reverse_port", return_value=True), \
             patch.object(adb_service, "dismiss_heads_up_notification", return_value=True), \
             patch.object(adb_service, "dismiss_popups", return_value=True), \
             patch.object(adb_service, "ensure_landing_or_search", return_value=True), \
             patch.object(adb_service, "open_chat_screen", return_value=True), \
             patch.object(adb_service, "scan_chat_friends_and_filter", side_effect=[mock_candidates, [], [], [], []]), \
             patch.object(adb_service, "unfollow_friend", return_value=True), \
             patch.object(adb_service, "scroll_down", return_value=True), \
             patch("asyncio.sleep", return_value=None), \
             patch("time.sleep", return_value=None):

            await bulk_unfollow_engine.run_unfollow_workflow("dev1", filter_type="no_streak", select_all=True)

            assert state_machine.current_state in [AppState.COMPLETED, AppState.READY, AppState.IDLE]
            assert not bulk_unfollow_engine.is_running

    asyncio.run(_test())

def test_inactivity_custom_days_threshold():
    """Verify scan_chat_friends_and_filter evaluates custom days_threshold accurately"""
    sample_xml = """<hierarchy>
        <node bounds="[0,250][720,380]" resource-id="com.snapchat.android:id/ff_item">
            <node bounds="[100,260][400,300]" text="InactiveFriend1" class="javaClass" />
            <node bounds="[100,310][400,350]" text="opened 2w ago" />
        </node>
        <node bounds="[0,400][720,530]" resource-id="com.snapchat.android:id/ff_item">
            <node bounds="[100,410][400,450]" text="RecentFriend2" class="javaClass" />
            <node bounds="[100,460][400,500]" text="new chat 3d ago" />
        </node>
    </hierarchy>"""

    with patch.object(adb_service, "dump_ui_hierarchy", return_value=sample_xml):
        # 1. Threshold = 7 days: "2w" (14 days) should match; "3d" should NOT match
        candidates_7d = adb_service.scan_chat_friends_and_filter("dev1", filter_type="inactive", days_threshold=7)
        assert len(candidates_7d) == 1
        assert candidates_7d[0]["name"] == "InactiveFriend1"

        # 2. Threshold = 30 days: neither 14d nor 3d exceeds 30d
        candidates_30d = adb_service.scan_chat_friends_and_filter("dev1", filter_type="inactive", days_threshold=30)
        assert len(candidates_30d) == 0


def test_scan_chat_friends_excludes_groups_and_recommendations():
    """Verify scan_chat_friends_and_filter strictly ignores group chats and recommendation cards"""
    sample_xml = """<hierarchy>
        <!-- Group 1: Comma in names -->
        <node bounds="[0,464][720,591]">
            <node bounds="[100,470][500,510]" text="OLAWALE✨🫶, Mr•Jalil✨" />
            <node bounds="[100,520][500,560]" text="Delivered" content-desc="Received from OLAWALE✨🫶" />
        </node>
        <!-- Group 2: Activity marker 'Received from' -->
        <node bounds="[0,600][720,720]">
            <node bounds="[100,610][500,650]" text="StudySquad" />
            <node bounds="[100,660][500,700]" text="Received from Alex" />
        </node>
        <!-- Recommendation row with feed_cross_button and phone number -->
        <node bounds="[0,730][720,850]">
            <node bounds="[600,740][650,790]" text="feed_cross_button" />
            <node bounds="[100,740][400,780]" text="0300 4177459" />
        </node>
        <!-- Genuine 1-on-1 friend without streak -->
        <node bounds="[0,860][720,980]">
            <node bounds="[100,870][400,910]" text="Hamza Tariq" />
            <node bounds="[100,920][400,960]" text="opened 5d ago" />
        </node>
        <!-- Friend with active streak (🔥) -->
        <node bounds="[0,990][720,1110]">
            <node bounds="[100,1000][400,1040]" text="Bilal Ahmed" />
            <node bounds="[500,1000][560,1040]" text="24🔥" />
            <node bounds="[100,1050][400,1090]" text="delivered 2h ago" />
        </node>
    </hierarchy>"""

    with patch.object(adb_service, "dump_ui_hierarchy", return_value=sample_xml):
        candidates = adb_service.scan_chat_friends_and_filter("dev1", filter_type="no_streak")
        # Should ONLY detect 'Hamza Tariq'
        # Groups (OLAWALE..., StudySquad), Phone (0300 4177459), and Streak (Bilal Ahmed) must be excluded!
        assert len(candidates) == 1
        assert candidates[0]["name"] == "Hamza Tariq"


def test_find_remove_confirmation_button():
    """Verify find_remove_confirmation_button reliably locates custom-drawn Remove button in Snapchat dialog"""
    # Exact Snapchat alert dialog structure where Remove button is an unlabelled View above cancel_button
    snapchat_dialog_xml = """<hierarchy>
        <node bounds="[114,649][606,1062]" resource-id="com.snapchat.android:id/dialog_content" class="android.widget.LinearLayout">
            <node bounds="[114,649][606,808]" text="Are you sure you want to remove user as a friend?" resource-id="com.snapchat.android:id/alert_dialog_title" class="android.widget.TextView" />
            <node bounds="[114,840][606,946]" text="" resource-id="" class="android.view.View" clickable="true" />
            <node bounds="[114,962][606,1062]" text="Cancel" resource-id="com.snapchat.android:id/cancel_button" class="android.widget.TextView" clickable="true" />
        </node>
    </hierarchy>"""

    with patch.object(adb_service, "dump_ui_hierarchy", return_value=snapchat_dialog_xml):
        elem = adb_service.find_remove_confirmation_button("dev1")
        assert elem is not None
        assert elem["bounds"] == (114, 840, 606, 946)
        assert elem["center"] == (360, 893)

    # Standard explicit text dialog test
    standard_dialog_xml = """<hierarchy>
        <node bounds="[200,900][520,980]" text="Remove" resource-id="android:id/button1" class="android.widget.Button" clickable="true" />
        <node bounds="[200,1000][520,1080]" text="Cancel" resource-id="android:id/button2" class="android.widget.Button" clickable="true" />
    </hierarchy>"""

    with patch.object(adb_service, "dump_ui_hierarchy", return_value=standard_dialog_xml):
        elem = adb_service.find_remove_confirmation_button("dev1")
        assert elem is not None
        assert elem["bounds"] == (200, 900, 520, 980)
        assert elem["center"] == (360, 940)


def test_unfollow_friend_full_flow():
    """Verify unfollow_friend executes 4 steps including confirmation modal click"""
    taps = []
    def mock_tap_human(dev, x, y, bounds=None):
        taps.append((x, y))

    with patch.object(adb_service, "_run_cmd", return_value=MagicMock(returncode=0)), \
         patch.object(adb_service, "find_element", side_effect=[
             {"center": (360, 1024), "bounds": (0, 986, 720, 1062)}, # Manage Friendship
             {"center": (360, 921), "bounds": (0, 883, 720, 959)},   # Remove Friend
         ]), \
         patch.object(adb_service, "find_remove_confirmation_button", return_value={
             "center": (360, 893), "bounds": (114, 840, 606, 946)
         }), \
         patch.object(adb_service, "input_tap_human", side_effect=mock_tap_human), \
         patch("time.sleep", return_value=None):

        success = adb_service.unfollow_friend("dev1", 250, 400)
        assert success is True
        assert (360, 1024) in taps # Manage Friendship tapped
        assert (360, 921) in taps  # Remove Friend tapped
        assert (360, 893) in taps  # Remove confirmation tapped


