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
        self._snapchat_version_cache: Dict[str, str] = {}

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

    def get_snapchat_version(self, device_id: str) -> str:
        """Retrieves and caches the installed Snapchat version from device (fallback: '14.29.0.50')"""
        if device_id in self._snapchat_version_cache:
            return self._snapchat_version_cache[device_id]

        try:
            res = self._run_cmd(
                [self.adb_path, "-s", device_id, "shell", "dumpsys", "package", "com.snapchat.android"],
                timeout=4
            )
            m = re.search(r"versionName=([0-9\.]+)", res.stdout or "")
            if m:
                ver = m.group(1)
                self._snapchat_version_cache[device_id] = ver
                return ver
        except Exception:
            pass

        self._snapchat_version_cache[device_id] = "14.29.0.50"
        return "14.29.0.50"

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
                    snap_ver = self.get_snapchat_version(device_id)
                    devices.append(DeviceInfo(
                        device_id=device_id,
                        model=model,
                        snapchat_version=snap_ver,
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
        Executes a human-like finger tap with organic spatial jitter within element bounds
        using native Android tap event dispatch to guarantee reliable click listener firing.
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

            cmd = [
                self.adb_path, "-s", device_id, "shell",
                "input", "tap", str(target_x), str(target_y)
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

            # 1. Popups & Confirmation Dialogs Check (Explicit modal overlays)
            # Exclude section titles like 'Find Friends' on standard search screen!
            dialog_markers = [
                "clear recent searches", "clear search history",
                "sync contacts", "sync your contacts",
                "turn on notifications", "snapchat is better with friends",
                "permission to access", "allow access to",
                "save your login info", "location permission",
                "wants to use your location", "snapchat wants to",
                "don't allow"
            ]
            has_dialog_text = any(dm in joined_texts or dm in joined_descs for dm in dialog_markers)
            has_native_dialog = any(k in joined_ids for k in ["parentpanel", "alerttitle"])

            if has_dialog_text or has_native_dialog:
                return "POPUP"

            # 2. Search Screen Check (If search-textfield or search-box is visible, we are on search page)
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
        'Cancel', 'Not now', 'Skip', 'Abandon', or dismissing dialogs.
        CRITICAL: Never blindly clicks the top back arrow or sends KEYCODE_BACK
        unless an actual dialog or popup is actively detected!
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return False

        try:
            xml_lower = xml_content.lower()

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

            # 1. Special check for "Abandon your Snapsterpiece" popup
            if "abandon your snapsterpiece" in xml_lower or "abandon snap" in xml_lower:
                # White 'Abandon' button is at center (360, 918)
                self.input_tap(device_id, 360, 918)
                time.sleep(0.8)
                return True

            # 2. Special check for "Add To Your Story?" dialog
            if "add to your story?" in xml_lower:
                # Click Cancel button
                for node in root.iter("node"):
                    txt = (node.attrib.get("text") or "").strip().lower()
                    res = (node.attrib.get("resource-id") or "").lower()
                    if txt == "cancel" or "cancel_button" in res:
                        pt = get_center(node.attrib.get("bounds", ""))
                        if pt:
                            self.input_tap(device_id, pt[0], pt[1])
                            time.sleep(0.8)
                            return True
                self.input_tap(device_id, 360, 1115)
                time.sleep(0.8)
                return True

            # 3. Special check for Lens+ / Snapchat+ subscription bottom sheet
            if "get lens+" in xml_lower or "exclusive lenses with lens+" in xml_lower or ("lens+" in xml_lower and "try" in xml_lower):
                # Tap outside the bottom sheet to dismiss it cleanly
                self.input_tap(device_id, 360, 250)
                time.sleep(0.6)
                return True

            # 4. Check for standard system/app Dialog overlays (alertTitle, dialog_content, parentPanel)
            has_dialog = any(k in xml_lower for k in [
                "alerttitle", "dialog_content", "parentpanel", "alert_dialog",
                "custompanel", "permission_allow_button"
            ])

            dismiss_targets = [
                "cancel", "not now", "skip", "deny", "dismiss",
                "later", "maybe later", "no thanks", "dont allow",
                "don't allow", "abandon", "discard"
            ]

            if has_dialog:
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

                # If inside a confirmed dialog with no matching button, send KEYCODE_BACK to dismiss dialog
                self.input_key(device_id, 4)
                time.sleep(0.8)
                return True

            # No popup or dialog detected; do nothing!
            return False
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
        - Checks whether user is already added (e.g., 'Added', 'Pending')
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

            # If target row was NOT found in the search results, it cannot be added or already added!
            if target_y is None:
                return {
                    "status": "NOT_FOUND",
                    "details": f"Target @{target_name} not found in search results."
                }

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

                # Must be vertically aligned with the target's row (within 65px)
                if abs(node_y - target_y) > 65:
                    continue

                if "add-friend-button" in res_id or "add_friend_button" in res_id or (txt in ["add", "+ add"] and "story" not in res_id):
                    buttons.append({"type": "ADD", "center": (node_x, node_y), "bounds": b})
                elif "subscribe-button" in res_id or txt == "subscribe":
                    buttons.append({"type": "SUBSCRIBE", "center": (node_x, node_y), "bounds": b})
                elif txt in ["added", "pending"] or desc in ["added", "pending"]:
                    status_labels.append({"status": txt or desc, "center": (node_x, node_y), "bounds": b})

            if buttons:
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
        - Directly taps Camera tab & swipes down to dismiss bottom drawers/memories.
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

            # If on another tab (Chat/Stories/Map) or memories sheet open, tap Camera tab & swipe down
            self.input_tap(device_id, 360, 1560)
            time.sleep(0.5)
            self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", "300", "360", "1200", "250"], timeout=3)
            time.sleep(0.8)
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

    def dismiss_heads_up_notification(self, device_id: str) -> bool:
        """Swipes up at top of screen to dismiss heads-up notification banners"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", "150", "360", "20", "180"]
            self._run_cmd(cmd, timeout=3)
            return True
        except Exception:
            return False

    def scroll_down(self, device_id: str, distance: int = 450) -> bool:
        """Smoothly scrolls the screen downwards with organic swipe velocity"""
        try:
            start_y = 1100
            end_y = max(100, start_y - distance)
            duration = random.randint(350, 480)
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", str(start_y), "360", str(end_y), str(duration)]
            self._run_cmd(cmd, timeout=4)
            time.sleep(random.uniform(0.5, 0.9))
            return True
        except Exception:
            return False

    def scroll_up(self, device_id: str, distance: int = 450) -> bool:
        """Smoothly scrolls the screen upwards with organic swipe velocity"""
        try:
            start_y = 400
            end_y = min(1500, start_y + distance)
            duration = random.randint(350, 480)
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", str(start_y), "360", str(end_y), str(duration)]
            self._run_cmd(cmd, timeout=4)
            time.sleep(random.uniform(0.5, 0.9))
            return True
        except Exception:
            return False

    def open_add_friends_page(self, device_id: str) -> bool:
        """Opens Add Friends screen from camera landing via the top-right Add Friends icon"""
        elem = (
            self.find_element(device_id, resource_id="neon_add_friend_button_container")
            or self.find_element(device_id, content_desc="Add Friends")
        )
        coords = elem["center"] if elem else (569, 122)
        bounds = elem["bounds"] if elem else None
        self.input_tap_human(device_id, coords[0], coords[1], bounds=bounds)
        time.sleep(1.2)
        xml = self.dump_ui_hierarchy(device_id) or ""
        return "quick add" in xml.lower() or "added me" in xml.lower() or "add friends" in xml.lower()

    def quick_add_batch(self, device_id: str, max_count: int = 5) -> List[str]:
        """Scans Quick Add suggestions on the Add Friends screen and taps + Add with human pacing"""
        added_names = []
        for _ in range(3):
            if len(added_names) >= max_count:
                break
            xml_content = self.dump_ui_hierarchy(device_id)
            if not xml_content:
                break

            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            def parse_bounds(bounds_str: str):
                m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                if len(m) == 2:
                    return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
                return None

            buttons = []
            for node in root.iter("node"):
                res_id = (node.attrib.get("resource-id") or "").lower()
                txt = (node.attrib.get("text") or "").strip().lower()
                desc = (node.attrib.get("content-desc") or "").strip().lower()
                b = parse_bounds(node.attrib.get("bounds", ""))
                if (b[2] - b[0] < 20) or (b[3] - b[1] < 20) or b[1] < 300:
                    continue
                is_add = (
                    "scu_search_action_button" in res_id
                    or "add-friend-button" in res_id
                    or (desc == "add" and "story" not in res_id)
                    or (txt in ["add", "+ add"] and "story" not in res_id)
                )
                if is_add:
                    center = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                    buttons.append({"center": center, "bounds": b})

            if not buttons:
                # Scroll down gently to reveal more suggestions
                self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", "1100", "360", "650", "400"], timeout=4)
                time.sleep(1.2)
                continue

            for btn in buttons:
                if len(added_names) >= max_count:
                    break
                self.input_tap_human(device_id, btn["center"][0], btn["center"][1], bounds=btn["bounds"])
                added_names.append(f"Suggestion #{len(added_names) + 1}")
                time.sleep(random.uniform(1.8, 3.2)) # Anti-ban human jitter between quick adds

            if len(added_names) < max_count:
                self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", "1100", "360", "650", "400"], timeout=4)
                time.sleep(1.2)

        return added_names

    def accept_incoming_requests(self, device_id: str, max_count: int = 5) -> List[str]:
        """Taps 'Accept' for incoming friend requests under the 'Added Me' section"""
        accepted = []
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return accepted

        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_content)

        def parse_bounds(bounds_str: str):
            m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(m) == 2:
                return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
            return None

        accept_btns = []
        for node in root.iter("node"):
            txt = (node.attrib.get("text") or "").strip().lower()
            desc = (node.attrib.get("content-desc") or "").strip().lower()
            b = parse_bounds(node.attrib.get("bounds", ""))
            if not b:
                continue
            if txt == "accept" or desc == "accept":
                center = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                accept_btns.append({"center": center, "bounds": b})

        for btn in accept_btns[:max_count]:
            self.input_tap_human(device_id, btn["center"][0], btn["center"][1], bounds=btn["bounds"])
            accepted.append(f"Follower #{len(accepted) + 1}")
            time.sleep(random.uniform(1.5, 2.5))

        return accepted

    def capture_snap_photo(self, device_id: str) -> bool:
        """Triggers hardware photo capture on Camera Landing screen"""
        elem = (
            self.find_element(device_id, resource_id="camera_capture_button")
            or self.find_element(device_id, content_desc="Take a Snap")
        )
        coords = elem["center"] if elem else (360, 1258)
        bounds = elem["bounds"] if elem else None
        self.input_tap_human(device_id, coords[0], coords[1], bounds=bounds)
        time.sleep(1.5)
        return True

    def apply_random_filter(self, device_id: str, swipes_count: Optional[int] = None) -> int:
        """Swipes horizontally across preview screen to apply artistic color or lens filter"""
        count = swipes_count if swipes_count is not None else random.randint(1, 3)
        for _ in range(count):
            # Swipe left-to-right (180 to 600) to select standard Snapchat free color filters (B&W, vintage, warm, etc.)
            self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "180", "750", "600", "750", "350"], timeout=4)
            time.sleep(random.uniform(0.4, 0.7))

            # Resilience check: If Lens+ paywall bottom sheet opens, tap outside to dismiss and swipe off it
            xml = self.dump_ui_hierarchy(device_id) or ""
            if "lens+" in xml.lower() or "snapchat+" in xml.lower() or "try now" in xml.lower():
                self.input_tap(device_id, 360, 250)
                time.sleep(0.4)
                # Swipe back to free filter
                self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "600", "750", "180", "750", "350"], timeout=4)
                time.sleep(0.4)
        return count

    def open_send_to_screen(self, device_id: str) -> bool:
        """Taps the Send To button from the Snap preview screen (auto-dismissing any modal dialogs)"""
        # Dismiss any unexpected location, Lens+, or permission modal first
        self.dismiss_popups(device_id)
        time.sleep(0.5)

        elem = (
            self.find_element(device_id, resource_id="sent_to_button_label_mode_view")
            or self.find_element(device_id, resource_id="send_btn")
            or self.find_element(device_id, text="Send To")
            or self.find_element(device_id, content_desc="Send To")
            or self.find_element(device_id, content_desc="Send")
            or self.find_element(device_id, resource_id="send_to_button")
            or self.find_element(device_id, resource_id="action_menu_send_button")
        )
        coords = elem["center"] if elem else (585, 1541)
        bounds = elem["bounds"] if elem else (459, 1515, 712, 1567)

        for attempt in range(2):
            self.input_tap_human(device_id, coords[0], coords[1], bounds=bounds)
            time.sleep(1.8)
            xml = self.dump_ui_hierarchy(device_id) or ""
            if "input_field_edit_text" in xml or "recents" in xml.lower() or "find friends" in xml.lower():
                return True
            coords = (585, 1541)
            bounds = None

        return True



    def select_recipients_and_send(self, device_id: str, select_all: bool = True, max_recipients: int = 15) -> int:
        """Selects recipients on Send To screen and dispatches the Snap"""
        # Dismiss any modal dialog (e.g. Add to Story or Public Story)
        self.dismiss_popups(device_id)
        time.sleep(0.4)

        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return 0

        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_content)

        def parse_bounds(bounds_str: str):
            m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(m) == 2:
                return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
            return None

        # Look for friend names in Send To screen
        selected_count = 0
        candidate_circles = []

        ignore_terms = [
            "send to", "all", "new friends", "new", "post to", "recents & suggested",
            "find friends", "my story", "my ai", "recently joined", "in my contacts",
            "stories", "just for friends", "friends, followers", "ok", "cancel"
        ]

        for node in root.iter("node"):
            txt = (node.attrib.get("text") or "").strip().lower()
            cls = (node.attrib.get("class") or "").lower()
            b = parse_bounds(node.attrib.get("bounds", ""))
            if not b:
                continue

            # Friend row names are in x=148..564, y > 700 (below Stories section)
            if b[0] >= 100 and b[2] <= 600 and b[1] >= 700 and b[3] <= 1500:
                if txt and not any(term in txt for term in ignore_terms):
                    # Selection circle is at x=680 on this row
                    row_center_y = (b[1] + b[3]) // 2
                    candidate_circles.append((680, row_center_y))

        # Remove duplicate Y coordinates
        unique_circles = []
        for c in candidate_circles:
            if not any(abs(c[1] - uc[1]) < 30 for uc in unique_circles):
                unique_circles.append(c)

        if not unique_circles:
            # Verified coordinates of friend selection circles below My Story on Infinix device
            unique_circles = [(680, 956), (680, 1056), (680, 1163), (680, 1462)]

        # Tap up to max_recipients
        limit = len(unique_circles) if select_all else min(max_recipients, len(unique_circles))
        for circle in unique_circles[:limit]:
            self.input_tap_human(device_id, circle[0], circle[1])
            selected_count += 1
            time.sleep(random.uniform(0.3, 0.6))

        time.sleep(0.6) # Human hesitation before pressing Send

        # Dismiss any unexpected story confirmation modal if triggered
        self.dismiss_popups(device_id)

        # Tap Send button (bottom right blue circular button with paper plane at bounds [623,1540][704,1567])
        send_elem = (
            self.find_element(device_id, resource_id="send_to_send_button")
            or self.find_element(device_id, resource_id="send_button")
            or self.find_element(device_id, content_desc="Send")
        )
        send_coords = send_elem["center"] if send_elem else (664, 1553)
        self.input_tap_human(device_id, send_coords[0], send_coords[1])
        time.sleep(2.0) # Wait for snap dispatch and clean return to camera screen
        return selected_count



    def open_chat_screen(self, device_id: str) -> bool:
        """Navigates to the Chat feed tab from camera landing"""
        chat_elem = (
            self.find_element(device_id, resource_id="hova_header_chat_icon")
            or self.find_element(device_id, content_desc="Chat")
        )
        if chat_elem:
            self.input_tap_human(device_id, chat_elem["center"][0], chat_elem["center"][1], bounds=chat_elem["bounds"])
        else:
            # Human swipe right to open Chat feed
            self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "120", "800", "620", "800", "300"], timeout=4)
        time.sleep(1.2)
        xml = self.dump_ui_hierarchy(device_id) or ""
        return "chat" in xml.lower() or "feed" in xml.lower() or "snap" in xml.lower()

    def scan_chat_friends_and_filter(self, device_id: str, filter_type: str = "no_streak", days_threshold: int = 17) -> List[dict]:
        """
        Scans friend items in Chat feed and filters according to rules:
        - 'no_streak': Friends without active 🔥 streak
        - 'inactive': Friends where timestamp indicates inactivity (e.g., '2w', '3w', '1mo')
        """
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return []

        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_content)

        def parse_bounds(bounds_str: str):
            m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(m) == 2:
                return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
            return None

        candidates = []
        all_nodes = list(root.iter("node"))

        # Find row containers (ff_item or rows with height 80-160px)
        row_bounds = []
        for node in all_nodes:
            res_id = (node.attrib.get("resource-id") or "").lower()
            b = parse_bounds(node.attrib.get("bounds", ""))
            if "ff_item" in res_id and b and (b[3] - b[1]) > 50:
                row_bounds.append(b)

        # Fallback if ff_item is not present
        if not row_bounds:
            for node in all_nodes:
                b = parse_bounds(node.attrib.get("bounds", ""))
                if b and (b[3] - b[1]) > 80 and b[1] > 200 and b[3] < 1450:
                    row_bounds.append(b)

        ignored_status_words = [
            "received", "opened", "delivered", "new chat", "new snap",
            "you are now friends", "double tap to snap", "camera reply",
            "avatar_container", "feed_cross_button", "feed_snap_", "feed_"
        ]

        for rb in row_bounds:
            row_texts = []
            friend_name = None

            for node in all_nodes:
                nb = parse_bounds(node.attrib.get("bounds", ""))
                if nb:
                    mid_y = (nb[1] + nb[3]) // 2
                    if rb[1] <= mid_y <= rb[3]:
                        t = (node.attrib.get("text") or "").strip()
                        d = (node.attrib.get("content-desc") or "").strip()
                        cls = (node.attrib.get("class") or "").strip()
                        if t: row_texts.append(t)
                        if d: row_texts.append(d)

                        # Prefer bold or javaClass for the actual friend display name
                        clean_candidate = t or d
                        lower_cand = clean_candidate.lower()
                        if clean_candidate and not any(ign in lower_cand for ign in ignored_status_words) and not clean_candidate.isdigit():
                            if not friend_name or cls == "javaClass":
                                friend_name = clean_candidate

            if not friend_name and row_texts:
                for candidate in row_texts:
                    if not any(ign in candidate.lower() for ign in ignored_status_words) and not candidate.isdigit():
                        friend_name = candidate
                        break

            if not friend_name:
                continue

            # Protected accounts
            if any(prot in friend_name.lower() for prot in ["my ai", "team snapchat"]):
                continue

            joined_row = " ".join(row_texts).lower()
            has_streak = ("🔥" in joined_row or "streak" in joined_row)
            is_inactive = any(marker in joined_row for marker in ["2w", "3w", "4w", "1mo", "2mo", "3mo", "weeks ago", "months ago"])

            matches = False
            reason = ""
            if filter_type == "no_streak" and not has_streak:
                matches = True
                reason = "No active streak emoji (🔥) found"
            elif filter_type == "inactive" and is_inactive:
                matches = True
                reason = f"Dormant timestamp detected (exceeds {days_threshold} days)"
            elif filter_type == "custom":
                matches = True
                reason = "Targeted custom friend match"

            if matches:
                center = (250, (rb[1] + rb[3]) // 2)
                candidates.append({
                    "name": friend_name,
                    "center": center,
                    "bounds": rb,
                    "reason": reason
                })

        return candidates

    def unfollow_friend(self, device_id: str, x: int, y: int) -> bool:
        """Executes full friendship removal sequence: Long press -> Manage Friendship -> Remove Friend -> Confirm Remove"""
        try:
            # 1. Long-press on friend row
            self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", str(x), str(y), str(x), str(y), "950"], timeout=4)
            time.sleep(1.2)

            # 2. Tap 'Manage Friendship'
            manage_elem = self.find_element(device_id, text="Manage Friendship") or self.find_element(device_id, text="Friendship")
            if manage_elem:
                self.input_tap_human(device_id, manage_elem["center"][0], manage_elem["center"][1], bounds=manage_elem.get("bounds"))
            else:
                self.input_tap_human(device_id, 360, 740)
            time.sleep(1.2)

            # 3. Tap 'Remove Friend'
            remove_elem = self.find_element(device_id, text="Remove Friend")
            if remove_elem:
                self.input_tap_human(device_id, remove_elem["center"][0], remove_elem["center"][1], bounds=remove_elem.get("bounds"))
            else:
                self.input_tap_human(device_id, 360, 1333)
            time.sleep(1.0)

            # 4. Tap 'Remove' in confirmation modal
            confirm_elem = self.find_element(device_id, text="Remove", exact=True) or self.find_element(device_id, resource_id="button1")
            if confirm_elem:
                self.input_tap_human(device_id, confirm_elem["center"][0], confirm_elem["center"][1], bounds=confirm_elem.get("bounds"))
            else:
                self.input_tap_human(device_id, 360, 892)
            time.sleep(1.5)
            return True
        except Exception:
            return False

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

