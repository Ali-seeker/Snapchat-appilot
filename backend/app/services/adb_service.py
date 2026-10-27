import subprocess
import shutil
import re
import time
import random
from typing import List, Dict, Optional
from ..models.schemas import DeviceInfo

class ADBService:
    def __init__(self):
        self.adb_path = shutil.which("adb") or "adb"

    def _run_cmd(self, cmd: List[str], timeout: int = 8) -> subprocess.CompletedProcess:
        """Executes subprocess with explicit UTF-8 encoding and error replacement to prevent Windows cp1252 crashes"""
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )

    def is_adb_available(self) -> bool:
        try:
            res = self._run_cmd([self.adb_path, "version"], timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    def list_devices(self) -> List[DeviceInfo]:
        devices: List[DeviceInfo] = []
        if not self.is_adb_available():
            return devices

        try:
            res = self._run_cmd([self.adb_path, "devices", "-l"], timeout=5)
            lines = res.stdout.strip().splitlines()
            for line in lines[1:]:
                line = line.strip()
                if not line or "offline" in line:
                    continue
                parts = line.split()
                device_id = parts[0]
                status = parts[1] if len(parts) > 1 else "unknown"
                if status == "device":
                    model_match = re.search(r"model:(\S+)", line)
                    model = model_match.group(1) if model_match else "Android Device"
                    devices.append(DeviceInfo(
                        device_id=device_id,
                        model=model,
                        is_connected=True
                    ))
                    # Ensure reverse port tunnel is continually kept alive for mobile companion
                    self.reverse_port(device_id)
        except Exception:
            pass

        return devices

    def reverse_port(self, device_id: str, port: int = 8000) -> bool:
        try:
            res = self._run_cmd(
                [self.adb_path, "-s", device_id, "reverse", f"tcp:{port}", f"tcp:{port}"],
                timeout=5
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_battery(self, device_id: str) -> Optional[int]:
        try:
            res = self._run_cmd(
                [self.adb_path, "-s", device_id, "shell", "dumpsys", "battery"],
                timeout=5
            )
            m = re.search(r"level:\s*(\d+)", res.stdout)
            if m:
                return int(m.group(1))
        except Exception:
            pass
        return None

    def launch_snapchat(self, device_id: str) -> bool:
        """Launches Snapchat main activity deterministically using Android Activity Manager without injecting random touches"""
        try:
            cmd = [
                self.adb_path, "-s", device_id, "shell",
                "am", "start", "-a", "android.intent.action.MAIN",
                "-c", "android.intent.category.LAUNCHER",
                "-p", "com.snapchat.android"
            ]
            res = self._run_cmd(cmd, timeout=8)
            return res.returncode == 0
        except Exception:
            return False

    def stop_snapchat(self, device_id: str) -> bool:
        """Force stops Snapchat"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "am", "force-stop", "com.snapchat.android"]
            res = self._run_cmd(cmd, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def is_snapchat_running(self, device_id: str) -> bool:
        """Checks if Snapchat is currently visible in foreground"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "dumpsys", "window"]
            res = self._run_cmd(cmd, timeout=5)
            return "com.snapchat.android" in res.stdout
        except Exception:
            return False

    def input_tap(self, device_id: str, x: int, y: int) -> bool:
        """Executes hardware tap via adb input"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "tap", str(x), str(y)]
            res = self._run_cmd(cmd, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def input_tap_human(self, device_id: str, x: int, y: int, bounds: Optional[tuple[int, int, int, int]] = None) -> bool:
        """
        Executes a human-like finger tap with realistic touch duration (55-115ms)
        and subtle organic finger placement within element bounds rather than robotic center tap.
        """
        try:
            if bounds:
                x1, y1, x2, y2 = bounds
                margin_x = max(2, (x2 - x1) // 6)
                margin_y = max(2, (y2 - y1) // 6)
                target_x = random.randint(x1 + margin_x, x2 - margin_x)
                target_y = random.randint(y1 + margin_y, y2 - margin_y)
            else:
                target_x = x + random.randint(-3, 3)
                target_y = y + random.randint(-3, 3)

            press_duration = random.randint(60, 115) # Realistic human touch contact time
            cmd = [
                self.adb_path, "-s", device_id, "shell",
                "input", "swipe", str(target_x), str(target_y), str(target_x), str(target_y), str(press_duration)
            ]
            res = self._run_cmd(cmd, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def input_text(self, device_id: str, text: str) -> bool:
        """Types text via adb input text, escaping whitespace and shell characters"""
        try:
            safe_text = text.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'")
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "text", safe_text]
            res = self._run_cmd(cmd, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def input_text_human(self, device_id: str, text: str, min_delay: float = 0.08, max_delay: float = 0.20) -> bool:
        """
        Types text character-by-character with realistic human typing speed
        and natural timing variations to bypass heuristic bot detection.
        """
        try:
            for char in text:
                safe_char = "%s" if char == " " else re.escape(char) if char in ["&", "'", '"', "(", ")", ";", "|", "<", ">", "$", "`", "\\"] else char
                cmd = [self.adb_path, "-s", device_id, "shell", "input", "text", safe_char]
                self._run_cmd(cmd, timeout=4)
                time.sleep(random.uniform(min_delay, max_delay))
            return True
        except Exception:
            return False

    def input_key(self, device_id: str, keycode: int) -> bool:
        """Sends keyevent: 66=Enter, 4=Back, 3=Home, 67=Backspace, 111=Escape"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "keyevent", str(keycode)]
            res = self._run_cmd(cmd, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def dump_ui_hierarchy(self, device_id: str) -> Optional[str]:
        """Dumps UI XML hierarchy from device screen and returns as string with explicit UTF-8 decoding"""
        try:
            self._run_cmd(
                [self.adb_path, "-s", device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"],
                timeout=8
            )
            res = self._run_cmd(
                [self.adb_path, "-s", device_id, "shell", "cat", "/sdcard/window_dump.xml"],
                timeout=6
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass
        return None

    def find_element(
        self,
        device_id: str,
        resource_id: Optional[str] = None,
        text: Optional[str] = None,
        content_desc: Optional[str] = None,
        class_name: Optional[str] = None,
        target_name: Optional[str] = None,
        exact: bool = False
    ) -> Optional[dict]:
        """
        Dynamically locates an interactive UI element strictly by its resource-id,
        text, or content-desc attributes in the live XML hierarchy.
        Filters out 'Clear All' in Recents when searching for clear-button.
        Returns a dict: {'center': (x, y), 'bounds': (x1, y1, x2, y2), 'resource_id': ..., 'text': ...}
        Never uses hardcoded coordinates.
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return None

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            def parse_bounds(bounds_str: str) -> Optional[tuple[int, int, int, int]]:
                m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                if len(m) == 2:
                    x1, y1 = int(m[0][0]), int(m[0][1])
                    x2, y2 = int(m[1][0]), int(m[1][1])
                    if (x2 - x1) > 10 and (y2 - y1) > 10 and (x1 > 0 or y1 > 0 or x2 > 0 or y2 > 0):
                        return (x1, y1, x2, y2)
                return None

            target_y = None
            if target_name:
                t_clean = target_name.lower().replace("@", "")
                exact_match_y = None
                for node in root.iter("node"):
                    txt = (node.attrib.get("text") or "").strip().lower()
                    desc = (node.attrib.get("content-desc") or "").strip().lower()
                    if txt == t_clean or desc == t_clean:
                        b = parse_bounds(node.attrib.get("bounds", ""))
                        if b:
                            exact_match_y = (b[1] + b[3]) // 2
                            break
                    elif t_clean in txt or t_clean in desc:
                        b = parse_bounds(node.attrib.get("bounds", ""))
                        if b and target_y is None:
                            target_y = (b[1] + b[3]) // 2
                if exact_match_y is not None:
                    target_y = exact_match_y

            candidates = []
            for node in root.iter("node"):
                node_res = node.attrib.get("resource-id") or ""
                node_txt = node.attrib.get("text") or ""
                node_desc = node.attrib.get("content-desc") or ""
                node_cls = node.attrib.get("class") or ""
                bounds = parse_bounds(node.attrib.get("bounds", ""))
                if not bounds:
                    continue

                # Safety: Never mistake 'Clear All' in Recents section for the text clear button
                if (resource_id and "clear" in resource_id.lower()) or (content_desc and "clear" in content_desc.lower()):
                    if "clear all" in node_desc.lower() or "action-button" in node_res.lower() or "recents" in node_desc.lower():
                        continue

                matched = False
                if resource_id:
                    if exact:
                        matched = (resource_id.lower() == node_res.lower())
                    else:
                        matched = (resource_id.lower() in node_res.lower())

                if not matched and text:
                    if exact:
                        matched = (text.lower() == node_txt.lower())
                    else:
                        matched = (text.lower() in node_txt.lower())

                if not matched and content_desc:
                    if exact:
                        matched = (content_desc.lower() == node_desc.lower())
                    else:
                        matched = (content_desc.lower() in node_desc.lower())

                if matched and class_name:
                    if class_name.lower() not in node_cls.lower():
                        matched = False

                if matched:
                    center = ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
                    candidates.append({
                        "center": center,
                        "bounds": bounds,
                        "resource_id": node_res,
                        "text": node_txt,
                        "content_desc": node_desc,
                        "class": node_cls
                    })

            if not candidates:
                return None

            if target_y is not None:
                candidates.sort(key=lambda item: abs(item["center"][1] - target_y))

            return candidates[0]
        except Exception:
            return None

    def find_bounds(self, device_id: str, query: str, target_name: Optional[str] = None) -> Optional[tuple[int, int]]:
        """
        Parses UI XML hierarchy to find center (x, y) coordinates for target text or id.
        Filters out dummy elements with [0,0][0,0] bounds.
        Supports target_name row correlation for Add/Subscribe buttons.
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return None

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            q_lower = query.lower()

            def get_valid_center(bounds_str: str) -> Optional[tuple[int, int]]:
                m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                if len(m) == 2:
                    x1, y1 = int(m[0][0]), int(m[0][1])
                    x2, y2 = int(m[1][0]), int(m[1][1])
                    if (x2 - x1) > 10 and (y2 - y1) > 10 and (x1 > 0 or y1 > 0 or x2 > 0 or y2 > 0):
                        return ((x1 + x2) // 2, (y1 + y2) // 2)
                return None

            # 1. Specialized query: "search"
            if q_lower == "search":
                for node in root.iter("node"):
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    desc = (node.attrib.get("content-desc") or "").lower()
                    txt = (node.attrib.get("text") or "").lower()
                    if ("search-textfield" in res_id or "search-box" in res_id or "search_bar" in res_id
                            or "hova_header_search_icon" in res_id or desc == "search" or txt == "search"):
                        c = get_valid_center(node.attrib.get("bounds", ""))
                        if c:
                            return c

            # 2. Specialized query: "add" or "subscribe"
            if q_lower in ["add", "add-friend-button", "subscribe", "subscribe-button"]:
                target_y = None
                if target_name:
                    t_clean = target_name.lower().replace("@", "")
                    for node in root.iter("node"):
                        txt = (node.attrib.get("text") or "").lower()
                        desc = (node.attrib.get("content-desc") or "").lower()
                        res_id = (node.attrib.get("resource-id") or "").lower()
                        if t_clean in txt or t_clean in desc:
                            c = get_valid_center(node.attrib.get("bounds", ""))
                            if c:
                                target_y = c[1]
                                break

                add_candidates = []
                for node in root.iter("node"):
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    txt = (node.attrib.get("text") or "").lower()
                    desc = (node.attrib.get("content-desc") or "").lower()

                    is_valid_btn = (
                        "add-friend-button" in res_id
                        or "add_friend_button" in res_id
                        or "subscribe-button" in res_id
                        or (txt in ["add", "+ add", "add friend"] and "story" not in res_id and "invite" not in res_id)
                    )

                    if is_valid_btn:
                        c = get_valid_center(node.attrib.get("bounds", ""))
                        if c:
                            add_candidates.append(c)

                if add_candidates:
                    if target_y is not None:
                        add_candidates.sort(key=lambda pt: abs(pt[1] - target_y))
                    return add_candidates[0]
                return None  # Do NOT fall through to arbitrary string search for add button

            # 3. Specialized query: "clear" (never match 'Clear All' in Recents)
            if q_lower in ["clear", "clear-button"]:
                for node in root.iter("node"):
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    desc = (node.attrib.get("content-desc") or "").lower()
                    if ("clear-button" in res_id or "clear_button" in res_id) and "action-button" not in res_id and "clear all" not in desc:
                        c = get_valid_center(node.attrib.get("bounds", ""))
                        if c:
                            return c
                return None

            # 4. General fallback search across text, content-desc, and resource-id
            for node in root.iter("node"):
                text = (node.attrib.get("text") or "").lower()
                desc = (node.attrib.get("content-desc") or "").lower()
                res_id = (node.attrib.get("resource-id") or "").lower()

                # Safety: Skip recents Clear All button
                if q_lower == "clear" and "clear all" in desc:
                    continue

                if q_lower in text or q_lower in desc or q_lower in res_id:
                    c = get_valid_center(node.attrib.get("bounds", ""))
                    if c:
                        return c
        except Exception:
            pass
        return None

    def get_search_field_text(self, device_id: str) -> Optional[str]:
        """Returns the current string inside search-textfield, or None if not on search page"""
        elem = self.find_element(device_id, resource_id="search-textfield")
        if elem:
            return elem.get("text", "")
        return None

    def detect_screen_state(self, device_id: str) -> str:
        """
        Classifies current screen state on device using comprehensive hierarchy analysis:
        - 'CAMERA_LANDING': Primary camera viewfinder screen with search & capture button
        - 'SEARCH_PAGE': Search textfield active / search screen
        - 'POPUP': Dialog, confirmation modal ('Clear recent searches?'), or system permission
        - 'PROFILE_PAGE': User's own Bitmoji / account profile screen
        - 'UNEXPECTED_SCREEN': Any other unrecognized screen
        - 'APP_NOT_RUNNING': Snapchat is not active in foreground
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return "UNKNOWN"

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            packages = {node.attrib.get("package", "") for node in root.iter("node")}
            if "com.snapchat.android" not in packages:
                return "APP_NOT_RUNNING"

            all_texts = []
            all_descs = []
            all_ids = []
            for node in root.iter("node"):
                t = (node.attrib.get("text") or "").lower()
                d = (node.attrib.get("content-desc") or "").lower()
                r = (node.attrib.get("resource-id") or "").lower()
                if t: all_texts.append(t)
                if d: all_descs.append(d)
                if r: all_ids.append(r)

            joined_texts = " ".join(all_texts)
            joined_descs = " ".join(all_descs)
            joined_ids = " ".join(all_ids)

            # 1. Popups & Confirmation Dialogs Check (Must take priority over underlying screens!)
            popup_triggers = [
                "clear recent searches", "clear search history",
                "find friends", "sync contacts", "find your friends",
                "turn on notifications", "allow access", "what's new",
                "snapchat is better with friends", "contacts access",
                "connect with friends", "save your login info",
                "location permission", "permission to access"
            ]
            for trigger in popup_triggers:
                if trigger in joined_texts or trigger in joined_descs:
                    return "POPUP"

            # Check for native dialog elements
            if "parentpanel" in joined_ids or "alerttitle" in joined_ids or "dialog" in joined_ids:
                return "POPUP"

            # 2. Search Screen Check
            if "search-textfield" in joined_ids or "search-box" in joined_ids:
                return "SEARCH_PAGE"

            # 3. Profile Screen Check
            if ("my profile" in joined_texts or "bitmoji" in joined_ids or "settings_button" in joined_ids or "profile_avatar" in joined_ids):
                if "camera_capture_button" not in joined_ids:
                    return "PROFILE_PAGE"

            # 4. Camera Landing Screen Check
            if ("hova_header_search_icon" in joined_ids or "camera_capture_button" in joined_ids or "neon_header_avatar" in joined_ids):
                return "CAMERA_LANDING"

            return "UNEXPECTED_SCREEN"
        except Exception:
            return "UNKNOWN"

    def dismiss_popups(self, device_id: str) -> bool:
        """
        Attempts to dismiss any detected modal, popup, or overlay by clicking
        'Cancel', 'Not now', 'Skip', '✕', or pressing KEYCODE_BACK.
        Safely cancels confirmation dialogs without clearing search history.
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return False

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            def get_center(bounds_str: str) -> Optional[tuple[int, int]]:
                m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                if len(m) == 2:
                    x1, y1 = int(m[0][0]), int(m[0][1])
                    x2, y2 = int(m[1][0]), int(m[1][1])
                    if (x2 - x1) > 10 and (y2 - y1) > 10:
                        return ((x1 + x2) // 2, (y1 + y2) // 2)
                return None

            dismiss_targets = [
                "cancel", "not now", "skip", "deny", "dismiss",
                "later", "maybe later", "no thanks", "close", "dont allow",
                "don't allow"
            ]

            # 1. Look for explicit dismiss text button (prioritize Cancel)
            for node in root.iter("node"):
                t = (node.attrib.get("text") or "").strip().lower()
                d = (node.attrib.get("content-desc") or "").strip().lower()
                r = (node.attrib.get("resource-id") or "").lower()

                if t in dismiss_targets or d in dismiss_targets or "close_button" in r or "dismiss_button" in r:
                    pt = get_center(node.attrib.get("bounds", ""))
                    if pt:
                        self.input_tap(device_id, pt[0], pt[1])
                        time.sleep(0.8)
                        return True

            # 2. Look for cross/close icon
            for node in root.iter("node"):
                d = (node.attrib.get("content-desc") or "").strip().lower()
                if d in ["close", "cancel", "dismiss", "back"]:
                    pt = get_center(node.attrib.get("bounds", ""))
                    if pt:
                        self.input_tap(device_id, pt[0], pt[1])
                        time.sleep(0.8)
                        return True

            # 3. Fallback: send KEYCODE_BACK (Key 4) to dismiss dialog
            self.input_key(device_id, 4)
            time.sleep(0.8)
            return True
        except Exception:
            return False

    def close_search_to_camera(self, device_id: str, max_retries: int = 3) -> bool:
        """
        Gracefully closes the search interface and returns to the primary CAMERA_LANDING screen
        by tapping the Cancel button or sending Back key, verifying the screen state transition.
        """
        for _ in range(max_retries):
            state = self.detect_screen_state(device_id)
            if state == "CAMERA_LANDING":
                return True

            # Try tapping the explicit 'Cancel' button in search header
            cancel_elem = (
                self.find_element(device_id, resource_id="dismiss-button")
                or self.find_element(device_id, text="Cancel", exact=True)
                or self.find_element(device_id, content_desc="Cancel", exact=True)
            )
            if cancel_elem:
                self.input_tap_human(device_id, cancel_elem["center"][0], cancel_elem["center"][1], bounds=cancel_elem.get("bounds"))
                time.sleep(0.8)
            else:
                self.input_key(device_id, 4)
                time.sleep(0.8)

            state = self.detect_screen_state(device_id)
            if state == "CAMERA_LANDING":
                return True

        return self.detect_screen_state(device_id) == "CAMERA_LANDING"

    def inspect_search_result(self, device_id: str, target_name: str) -> dict:
        """
        Deeply inspects the search results screen for a given target username:
        - Identifies target row matching username or display name
        - Checks whether Add Friend button exists
        - Checks whether user is already added (e.g., 'Added', 'Pending', 'Friends')
        - Checks whether Subscribe button exists (for Snap Stars)
        - Returns a structured dictionary with actionability status:
          'CAN_ADD', 'ALREADY_FRIEND', 'CAN_SUBSCRIBE', or 'NOT_FOUND'
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return {"status": "NOT_FOUND", "details": "Failed to dump UI hierarchy"}

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            def parse_bounds(bounds_str: str) -> Optional[tuple[int, int, int, int]]:
                m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                if len(m) == 2:
                    x1, y1 = int(m[0][0]), int(m[0][1])
                    x2, y2 = int(m[1][0]), int(m[1][1])
                    if (x2 - x1) > 10 and (y2 - y1) > 10:
                        return (x1, y1, x2, y2)
                return None

            t_clean = target_name.lower().replace("@", "").strip()

            target_y = None
            exact_found = False
            for node in root.iter("node"):
                txt = (node.attrib.get("text") or "").strip().lower()
                desc = (node.attrib.get("content-desc") or "").strip().lower()
                res_id = (node.attrib.get("resource-id") or "").lower()

                if "result-title" in res_id or "result-subtitle" in res_id or not res_id:
                    if txt == t_clean or desc == t_clean:
                        b = parse_bounds(node.attrib.get("bounds", ""))
                        if b:
                            target_y = (b[1] + b[3]) // 2
                            exact_found = True
                            break
                    elif not exact_found and (t_clean in txt or t_clean in desc):
                        b = parse_bounds(node.attrib.get("bounds", ""))
                        if b and target_y is None:
                            target_y = (b[1] + b[3]) // 2

            buttons = []
            status_labels = []

            for node in root.iter("node"):
                res_id = (node.attrib.get("resource-id") or "").lower()
                txt = (node.attrib.get("text") or "").strip().lower()
                desc = (node.attrib.get("content-desc") or "").strip().lower()
                b = parse_bounds(node.attrib.get("bounds", ""))
                if not b:
                    continue

                node_y = (b[1] + b[3]) // 2
                node_x = (b[0] + b[2]) // 2

                if target_y is not None and abs(node_y - target_y) > 65:
                    continue

                if "add-friend-button" in res_id or "add_friend_button" in res_id or (txt in ["add", "+ add"] and "story" not in res_id):
                    buttons.append({"type": "ADD", "center": (node_x, node_y), "bounds": b})
                elif "subscribe-button" in res_id or txt == "subscribe":
                    buttons.append({"type": "SUBSCRIBE", "center": (node_x, node_y), "bounds": b})
                elif txt in ["added", "pending", "friends"] or desc in ["added", "pending", "friends"]:
                    status_labels.append({"status": txt or desc, "center": (node_x, node_y), "bounds": b})

            if buttons:
                if target_y is not None:
                    buttons.sort(key=lambda item: abs(item["center"][1] - target_y))
                btn = buttons[0]
                if btn["type"] == "ADD":
                    return {
                        "status": "CAN_ADD",
                        "center": btn["center"],
                        "bounds": btn["bounds"],
                        "details": f"Found Add Friend button aligned with target @{target_name}"
                    }
                else:
                    return {
                        "status": "CAN_SUBSCRIBE",
                        "center": btn["center"],
                        "bounds": btn["bounds"],
                        "details": f"Found Subscribe button for creator @{target_name}"
                    }

            if status_labels:
                lbl = status_labels[0]["status"].capitalize()
                return {
                    "status": "ALREADY_FRIEND",
                    "details": f"Target @{target_name} is already {lbl}."
                }

            return {
                "status": "NOT_FOUND",
                "details": f"No Add Friend button or user found for query '@{target_name}'."
            }
        except Exception as e:
            return {"status": "NOT_FOUND", "details": f"Error parsing results: {str(e)}"}

    def ensure_landing_or_search(self, device_id: str, max_retries: int = 3) -> bool:
        """
        Guarantees that Snapchat is in a clean, valid state (Camera Landing or Search Page).
        If unexpected popups, profile page, or unrecognized screens appear:
        - Auto-dismisses popups or presses Back.
        - If still not settled, executes a clean application restart (kill -> relaunch)
        as requested by user.
        """
        for _ in range(max_retries):
            state = self.detect_screen_state(device_id)

            if state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                return True

            if state == "POPUP":
                self.dismiss_popups(device_id)
                time.sleep(1.0)
                state = self.detect_screen_state(device_id)
                if state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                    return True

            if state == "PROFILE_PAGE":
                self.input_key(device_id, 4)
                time.sleep(1.0)
                state = self.detect_screen_state(device_id)
                if state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                    return True

            # If still unexpected or app not running, perform Clean Recovery Restart
            self.stop_snapchat(device_id)
            time.sleep(1.0)
            self.launch_snapchat(device_id)
            time.sleep(2.5)

            post_state = self.detect_screen_state(device_id)
            if post_state == "POPUP":
                self.dismiss_popups(device_id)
                time.sleep(1.0)

        final_state = self.detect_screen_state(device_id)
        return final_state in ["CAMERA_LANDING", "SEARCH_PAGE"]

    def take_screenshot(self, device_id: str, local_path: str) -> bool:
        """Captures device screenshot and saves locally"""
        try:
            self._run_cmd(
                [self.adb_path, "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"],
                timeout=8
            )
            res = self._run_cmd(
                [self.adb_path, "-s", device_id, "pull", "/sdcard/screen.png", local_path],
                timeout=8
            )
            return res.returncode == 0
        except Exception:
            return False

adb_service = ADBService()

