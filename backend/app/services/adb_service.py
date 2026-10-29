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
        """Checks if Snapchat is currently running on the device"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "dumpsys", "window"]
            res = self._run_cmd(cmd, timeout=5)
            return "com.snapchat.android" in res.stdout
        except Exception:
            return False

    def is_snapchat_foreground(self, device_id: str) -> bool:
        """Checks if Snapchat is currently the active focused foreground window"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "dumpsys", "window", "windows"]
            res = self._run_cmd(cmd, timeout=5)
            output = res.stdout or ""
            for line in output.splitlines():
                if "mCurrentFocus" in line or "mFocusedApp" in line:
                    if "com.snapchat.android" in line:
                        return True
                    if "com.appilot.companion" in line:
                        return False
            return "com.snapchat.android" in output
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

    def hide_keyboard_if_present(self, device_id: str) -> bool:
        """Dismisses Android soft keyboard if currently displayed on screen"""
        try:
            res = self._run_cmd([self.adb_path, "-s", device_id, "shell", "dumpsys", "input_method"], timeout=4)
            if res.returncode == 0 and "mInputShown=true" in res.stdout:
                self.input_key(device_id, 4)  # KEYCODE_BACK dismisses the soft keyboard
                time.sleep(0.4)
                return True
        except Exception:
            pass
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

                    is_add_btn = (
                        "add-friend-button" in res_id
                        or "add_friend_button" in res_id
                        or (txt in ["add", "+ add", "add friend"] and "story" not in res_id and "invite" not in res_id and "upsell" not in res_id)
                    )
                    is_sub_btn = "subscribe-button" in res_id or txt == "subscribe"
                    is_valid_btn = (is_add_btn if q_lower in ["add", "add-friend-button"] else is_sub_btn)

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
        - 'CAMERA_LANDING': Primary camera viewfinder screen with capture button / camera page
        - 'SEARCH_PAGE': Search textfield active / search screen
        - 'SEND_TO': Send To recipient selection screen
        - 'SNAP_PREVIEW': Snap preview screen (photo captured, waiting to send or discard)
        - 'CHAT_FEED': Chat feed tab listing friend conversations
        - 'CHAT_CONVERSATION': Active 1-on-1 friend chat or group conversation thread
        - 'POPUP': Dialog, confirmation modal ('Clear recent searches?'), or system permission
        - 'PROFILE_PAGE': User's own Bitmoji / account profile screen
        - 'MEMORIES_DRAWER': Memories bottom sheet or grid
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

            # 1. Popups & Confirmation Dialogs Check
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

            # 2. Active Chat Conversation Check (Inside a friend chat thread)
            if any(k in joined_ids for k in ["chat_input_text_field", "chat_message_list", "chat_input_bar_camera"]):
                if "camera_capture_button" not in joined_ids:
                    return "CHAT_CONVERSATION"

            # 3. Add Friends Page Check (Strictly when NOT on camera landing)
            if "camera_capture_button" not in joined_ids:
                if any(k in joined_ids for k in ["add_friends_root", "add_friends_title", "add_friends_dismiss"]):
                    return "ADD_FRIENDS_PAGE"
                if "add friends" in joined_texts and any(k in joined_texts for k in ["find friends", "quick add", "all contacts"]):
                    return "ADD_FRIENDS_PAGE"

            # 4. Search Screen Check (If search-textfield or search-box is visible)
            if "search-textfield" in joined_ids or "search-box" in joined_ids:
                return "SEARCH_PAGE"

            # 4. Send To Screen Check
            if "send_to_confirmation_bar" in joined_ids or "send_to_send_button" in joined_ids or "send to?" in joined_texts or ("best friends" in joined_texts and "recents" in joined_texts):
                return "SEND_TO"

            # 5. Snap Preview Screen Check
            if "preview_back_discard_button" in joined_ids or "preview_frame" in joined_ids or "sent_to_button_label_mode_view" in joined_ids:
                return "SNAP_PREVIEW"

            # 6. Memories Check (Upward drawer on camera screen)
            if "memories_grid" in joined_ids or "memories_create_button" in joined_ids:
                return "MEMORIES_DRAWER"

            # 7. Profile Screen Check
            if ("my profile" in joined_texts or "bitmoji" in joined_ids or "settings_button" in joined_ids or "profile_avatar" in joined_ids):
                if "camera_capture_button" not in joined_ids and "camera_page" not in joined_ids:
                    return "PROFILE_PAGE"

            # 8. Camera Landing Screen Check
            if "camera_capture_button" in joined_ids or "camera_page" in joined_ids or "lenses_camera_carousel_list_view" in joined_ids:
                return "CAMERA_LANDING"

            # 9. Chat Feed Tab Check
            if "ff_item" in joined_ids or "ptr_container" in joined_ids or "chat_page" in joined_ids:
                return "CHAT_FEED"

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
        Gracefully closes search or Add Friends interface and returns to primary CAMERA_LANDING.
        Taps dismiss button / Cancel or sends Back key, verifying screen state transition.
        """
        for _ in range(max_retries):
            state = self.detect_screen_state(device_id)
            if state == "CAMERA_LANDING":
                return True

            self.hide_keyboard_if_present(device_id)

            if state == "MEMORIES_DRAWER":
                back_elem = self.find_element(device_id, resource_id="subscreen_top_left") or self.find_element(device_id, content_desc="Back arrow")
                if back_elem:
                    self.input_tap(device_id, back_elem["center"][0], back_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            dismiss_elem = (
                self.find_element(device_id, resource_id="add_friends/add_friends_dismiss")
                or self.find_element(device_id, resource_id="dismiss-button")
                or self.find_element(device_id, text="Cancel", exact=True)
                or self.find_element(device_id, content_desc="Cancel", exact=True)
            )
            if dismiss_elem:
                self.input_tap_human(device_id, dismiss_elem["center"][0], dismiss_elem["center"][1], bounds=dismiss_elem.get("bounds"))
                time.sleep(0.8)
            else:
                self.input_key(device_id, 4)
                time.sleep(0.8)

            if self.detect_screen_state(device_id) == "CAMERA_LANDING":
                return True

        return self.ensure_camera_landing(device_id)

    def inspect_search_result(self, device_id: str, target_name: str) -> dict:
        """
        Deeply inspects the search results screen for a given target username:
        - Automatically dismisses soft keyboard if obscuring results
        - Inspects candidate cells under 'Add Friends' (user-result-cell or rows)
        - Correctly correlates Add Friend button or 'Added' / 'Pending' status within the candidate's cell
        - Prioritizes Add Friend button over creator subscribe buttons
        - Returns structured dictionary:
          'CAN_ADD', 'ALREADY_FRIEND', 'CAN_SUBSCRIBE', or 'NOT_FOUND'
        """
        self.hide_keyboard_if_present(device_id)

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
            t_norm = re.sub(r"[^a-z0-9]", "", t_clean)

            candidates = []
            user_cells = []
            for node in root.iter("node"):
                res_id = (node.attrib.get("resource-id") or "").lower()
                if "user-result-cell" in res_id or "user_result_cell" in res_id:
                    user_cells.append(node)

            if user_cells:
                for idx, cell in enumerate(user_cells):
                    b_cell = parse_bounds(cell.attrib.get("bounds", ""))
                    c_username = ""
                    c_display = ""
                    add_btn = None
                    is_added = False

                    for child in cell.iter("node"):
                        c_res = (child.attrib.get("resource-id") or "").lower()
                        c_txt = (child.attrib.get("text") or "").strip()
                        c_desc = (child.attrib.get("content-desc") or "").strip()
                        b_child = parse_bounds(child.attrib.get("bounds", ""))

                        if "result-subtitle" in c_res:
                            c_username = c_txt or c_desc
                        elif "result-title" in c_res:
                            c_display = c_txt or c_desc

                        # Check add button
                        if (
                            "add-friend-button" in c_res
                            or "add_friend_button" in c_res
                            or (c_txt.lower() in ["add", "+ add", "add friend"] and "story" not in c_res and "upsell" not in c_res)
                        ):
                            if b_child:
                                cx = (b_child[0] + b_child[2]) // 2
                                cy = (b_child[1] + b_child[3]) // 2
                                add_btn = {"center": (cx, cy), "bounds": b_child}

                        # Check already added / pending / upsell
                        if c_txt.lower() in ["added", "pending"] or c_desc.lower() in ["added", "pending"] or "upsell" in c_res:
                            is_added = True

                    candidates.append({
                        "index": idx,
                        "username": c_username,
                        "display": c_display,
                        "add_btn": add_btn,
                        "is_added": is_added,
                        "bounds": b_cell,
                        "type": "USER_CELL"
                    })

            # If no user-result-cell found, fallback to row grouping by Y coordinates
            if not candidates:
                rows = {}
                for node in root.iter("node"):
                    b = parse_bounds(node.attrib.get("bounds", ""))
                    if not b:
                        continue
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    txt = (node.attrib.get("text") or "").strip()
                    desc = (node.attrib.get("content-desc") or "").strip()
                    cy = (b[1] + b[3]) // 2

                    bucket = round(cy / 65.0) * 65
                    if bucket not in rows:
                        rows[bucket] = {"username": "", "display": "", "add_btn": None, "is_added": False, "bounds": b, "index": len(rows)}

                    if "result-subtitle" in res_id or (txt and not rows[bucket]["username"] and not res_id):
                        rows[bucket]["username"] = txt or desc
                    elif "result-title" in res_id:
                        rows[bucket]["display"] = txt or desc

                    if (
                        "add-friend-button" in res_id
                        or "add_friend_button" in res_id
                        or (txt.lower() in ["add", "+ add", "add friend"] and "story" not in res_id and "upsell" not in res_id)
                    ):
                        cx = (b[0] + b[2]) // 2
                        rows[bucket]["add_btn"] = {"center": (cx, cy), "bounds": b}

                    if txt.lower() in ["added", "pending"] or desc.lower() in ["added", "pending"] or "upsell" in res_id:
                        rows[bucket]["is_added"] = True

                for k, v in sorted(rows.items()):
                    if v["add_btn"] or v["is_added"] or v["username"] or v["display"]:
                        candidates.append(v)

            # Score candidates against target
            scored = []
            for cand in candidates:
                u_clean = cand["username"].lower().replace("@", "").strip()
                u_norm = re.sub(r"[^a-z0-9]", "", u_clean)
                d_clean = cand["display"].lower().replace("@", "").strip()
                d_norm = re.sub(r"[^a-z0-9]", "", d_clean)

                score = 0
                if u_clean == t_clean or (t_norm and u_norm == t_norm):
                    score = 1000
                elif t_norm and d_norm == t_norm:
                    score = 800
                elif u_clean.startswith(t_clean) or t_clean in u_clean or (t_norm and t_norm in u_norm):
                    score = 600
                elif d_clean.startswith(t_clean) or t_clean in d_clean or (t_norm and t_norm in d_norm):
                    score = 400
                elif cand.get("index") == 0:
                    score = 200  # First result returned by search

                scored.append((score, cand))

            scored.sort(key=lambda x: x[0], reverse=True)

            if scored and scored[0][0] > 0:
                best_cand = scored[0][1]
                if best_cand["is_added"] or best_cand["add_btn"] is None:
                    return {
                        "status": "ALREADY_FRIEND",
                        "details": f"Target @{target_name} is already added or pending."
                    }
                if best_cand["add_btn"]:
                    return {
                        "status": "CAN_ADD",
                        "center": best_cand["add_btn"]["center"],
                        "bounds": best_cand["add_btn"]["bounds"],
                        "details": f"Found Add Friend button for @{best_cand['username'] or target_name}"
                    }

            # If no friend cell matched, check creator subscribe button as a last fallback
            for node in root.iter("node"):
                res_id = (node.attrib.get("resource-id") or "").lower()
                txt = (node.attrib.get("text") or "").strip().lower()
                if "subscribe-button" in res_id or txt == "subscribe":
                    b = parse_bounds(node.attrib.get("bounds", ""))
                    if b:
                        cx = (b[0] + b[2]) // 2
                        cy = (b[1] + b[3]) // 2
                        return {
                            "status": "CAN_SUBSCRIBE",
                            "center": (cx, cy),
                            "bounds": b,
                            "details": f"Found Subscribe button for creator @{target_name}"
                        }

            return {
                "status": "NOT_FOUND",
                "details": f"No Add Friend button or user found for query '@{target_name}'."
            }
        except Exception as e:
            return {"status": "NOT_FOUND", "details": f"Error parsing results: {str(e)}"}

    def ensure_landing_or_search(self, device_id: str, max_retries: int = 4) -> bool:
        """
        Guarantees that Snapchat is in a clean, valid state (Camera Landing or Search Page).
        If unexpected popups, active chat conversation, chat feed, profile page, send to, or snap preview appear:
        - Auto-dismisses keyboard and presses Back if inside a chat thread.
        - Taps Camera tab in bottom navigation bar if on Chat feed / Stories / other tabs.
        - Safely discards captured snap if on Snap Preview.
        - Backs out of Send To screen cleanly.
        - Auto-dismisses popups or presses Back for profile / memories drawer.
        - If still not settled on last attempt, executes clean application restart.
        """
        # Step 0: Ensure Snapchat is the active foreground app before touching screen
        if not self.is_snapchat_foreground(device_id):
            self.launch_snapchat(device_id)
            time.sleep(2.0)

        for attempt in range(max_retries):
            state = self.detect_screen_state(device_id)

            if state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                return True

            if state == "ADD_FRIENDS_PAGE":
                self.hide_keyboard_if_present(device_id)
                dismiss_elem = self.find_element(device_id, resource_id="add_friends/add_friends_dismiss")
                if dismiss_elem:
                    self.input_tap(device_id, dismiss_elem["center"][0], dismiss_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "SEND_TO":
                # Exit Send To back to Snap Preview
                back_elem = self.find_element(device_id, resource_id="subscreen_top_left") or self.find_element(device_id, content_desc="Back arrow")
                if back_elem:
                    self.input_tap(device_id, back_elem["center"][0], back_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "SNAP_PREVIEW":
                # Discard the captured snap preview to return to Camera Landing
                discard_elem = (
                    self.find_element(device_id, resource_id="preview_back_discard_button")
                    or self.find_element(device_id, content_desc="Discard")
                )
                coords = discard_elem["center"] if discard_elem else (62, 134)
                self.input_tap(device_id, coords[0], coords[1])
                time.sleep(0.8)

                # If confirmation modal 'Discard Snap?' appears, tap 'Discard'
                modal_discard = (
                    self.find_element(device_id, resource_id="discard_alert_dialog_discard_view")
                    or self.find_element(device_id, text="Discard")
                )
                if modal_discard:
                    self.input_tap(device_id, modal_discard["center"][0], modal_discard["center"][1])
                    time.sleep(0.8)
                continue

            if state == "CHAT_CONVERSATION":
                # Close soft keyboard first if open
                self.hide_keyboard_if_present(device_id)
                # Press Back key to return from conversation thread to Chat feed
                self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "CHAT_FEED":
                # Tap Camera tab in bottom navigation bar to switch to Camera Landing
                cam_elem = (
                    self.find_element(device_id, resource_id="ngs_camera_icon_container")
                    or self.find_element(device_id, content_desc="Camera")
                )
                coords = cam_elem["center"] if cam_elem else (359, 1541)
                self.input_tap(device_id, coords[0], coords[1])
                time.sleep(0.8)
                new_state = self.detect_screen_state(device_id)
                if new_state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                    return True
                # If tap didn't switch, try swipe right-to-left from Chat feed to Camera
                self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "550", "800", "150", "800", "250"], timeout=3)
                time.sleep(0.8)
                new_state = self.detect_screen_state(device_id)
                if new_state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                    return True

            if state == "MEMORIES_DRAWER":
                back_elem = self.find_element(device_id, resource_id="subscreen_top_left") or self.find_element(device_id, content_desc="Back arrow")
                if back_elem:
                    self.input_tap(device_id, back_elem["center"][0], back_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(1.0)
                continue

            if state == "POPUP":
                self.dismiss_popups(device_id)
                time.sleep(1.0)
                continue

            if state == "PROFILE_PAGE":
                self.input_key(device_id, 4)
                time.sleep(1.0)
                continue

            # If still unexpected on last attempt, perform Clean Recovery Restart
            if attempt == max_retries - 1:
                self.stop_snapchat(device_id)
                time.sleep(1.0)
                self.launch_snapchat(device_id)
                time.sleep(2.5)

        final_state = self.detect_screen_state(device_id)
        # If restarted on SNAP_PREVIEW, discard it to return to Camera Landing
        if final_state == "SNAP_PREVIEW":
            self.input_tap(device_id, 62, 134)
            time.sleep(0.8)
            modal_discard = self.find_element(device_id, text="Discard")
            if modal_discard:
                self.input_tap(device_id, modal_discard["center"][0], modal_discard["center"][1])
                time.sleep(0.8)
            final_state = self.detect_screen_state(device_id)

        return final_state in ["CAMERA_LANDING", "SEARCH_PAGE"]

    def ensure_camera_landing(self, device_id: str, max_retries: int = 4) -> bool:
        """
        Guarantees that Snapchat is strictly on the CAMERA_LANDING screen.
        If on Search, Add Friends, Chat, Stories, Memories, Send To, or Preview,
        it cleanly navigates back to the camera viewfinder.
        """
        if not self.is_snapchat_foreground(device_id):
            self.launch_snapchat(device_id)
            time.sleep(2.0)

        for attempt in range(max_retries):
            state = self.detect_screen_state(device_id)
            if state == "CAMERA_LANDING":
                return True

            if state in ["ADD_FRIENDS_PAGE", "SEARCH_PAGE"]:
                self.hide_keyboard_if_present(device_id)
                dismiss_elem = (
                    self.find_element(device_id, resource_id="add_friends/add_friends_dismiss")
                    or self.find_element(device_id, resource_id="dismiss-button")
                    or self.find_element(device_id, text="Cancel", exact=True)
                    or self.find_element(device_id, content_desc="Cancel", exact=True)
                )
                if dismiss_elem:
                    self.input_tap(device_id, dismiss_elem["center"][0], dismiss_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "SEND_TO":
                back_elem = self.find_element(device_id, resource_id="subscreen_top_left") or self.find_element(device_id, content_desc="Back arrow")
                if back_elem:
                    self.input_tap(device_id, back_elem["center"][0], back_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "SNAP_PREVIEW":
                discard_elem = (
                    self.find_element(device_id, resource_id="preview_back_discard_button")
                    or self.find_element(device_id, content_desc="Discard")
                )
                coords = discard_elem["center"] if discard_elem else (62, 134)
                self.input_tap(device_id, coords[0], coords[1])
                time.sleep(0.8)
                modal_discard = (
                    self.find_element(device_id, resource_id="discard_alert_dialog_discard_view")
                    or self.find_element(device_id, text="Discard")
                )
                if modal_discard:
                    self.input_tap(device_id, modal_discard["center"][0], modal_discard["center"][1])
                    time.sleep(0.8)
                continue

            if state == "CHAT_CONVERSATION":
                self.hide_keyboard_if_present(device_id)
                self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "CHAT_FEED":
                cam_elem = (
                    self.find_element(device_id, resource_id="ngs_camera_icon_container")
                    or self.find_element(device_id, content_desc="Camera")
                )
                coords = cam_elem["center"] if cam_elem else (359, 1541)
                self.input_tap(device_id, coords[0], coords[1])
                time.sleep(0.8)
                if self.detect_screen_state(device_id) == "CAMERA_LANDING":
                    return True
                self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "550", "800", "150", "800", "250"], timeout=3)
                time.sleep(0.8)
                if self.detect_screen_state(device_id) == "CAMERA_LANDING":
                    return True

            if state == "MEMORIES_DRAWER":
                back_elem = self.find_element(device_id, resource_id="subscreen_top_left") or self.find_element(device_id, content_desc="Back arrow")
                if back_elem:
                    self.input_tap(device_id, back_elem["center"][0], back_elem["center"][1])
                else:
                    self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if state == "POPUP":
                self.dismiss_popups(device_id)
                time.sleep(0.8)
                continue

            if state == "PROFILE_PAGE":
                self.input_key(device_id, 4)
                time.sleep(0.8)
                continue

            if attempt == max_retries - 1:
                self.stop_snapchat(device_id)
                time.sleep(1.0)
                self.launch_snapchat(device_id)
                time.sleep(2.5)

        final_state = self.detect_screen_state(device_id)
        if final_state == "SNAP_PREVIEW":
            self.input_tap(device_id, 62, 134)
            time.sleep(0.8)
            modal_discard = self.find_element(device_id, text="Discard")
            if modal_discard:
                self.input_tap(device_id, modal_discard["center"][0], modal_discard["center"][1])
                time.sleep(0.8)
            final_state = self.detect_screen_state(device_id)

        return final_state == "CAMERA_LANDING"

    def dismiss_heads_up_notification(self, device_id: str) -> bool:
        """
        Safely dismisses heads-up notification banners (e.g., WhatsApp, system popups)
        ONLY if an external notification overlay is actually detected.
        CRITICAL: Never blindly swipe up on Snapchat Camera screen, as upward swipes trigger
        Snapchat Memories drawer!
        """
        try:
            state = self.detect_screen_state(device_id)
            if state in ["CAMERA_LANDING", "SEARCH_PAGE"]:
                return False

            xml_content = self.dump_ui_hierarchy(device_id)
            if not xml_content:
                return False

            xml_lower = xml_content.lower()
            if any(k in xml_lower for k in ["heads_up_notification", "notification_container", "status_bar_latest_event_content"]):
                cmd = [self.adb_path, "-s", device_id, "shell", "input", "swipe", "360", "120", "360", "10", "150"]
                self._run_cmd(cmd, timeout=3)
                time.sleep(0.5)
                return True
            return False
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
        """
        Scans Quick Add / Find Friends suggestions on the Add Friends screen and taps '+ Add' with human pacing.
        - Automatically dismisses soft keyboard if active
        - Strictly isolates the 'Find Friends' / 'Quick Add' section and filters out the 'Added Me' section
        - Rejects any buttons in 'Added Me' (e.g. Camera / Snap back buttons)
        - Rejects 'Invite To Snapchat' buttons
        - Targets genuine '+ Add' buttons (yellow background pill with person icon and '+')
        """
        self.hide_keyboard_if_present(device_id)
        added_names = []

        for attempt in range(3):
            if len(added_names) >= max_count:
                break

            xml_content = self.dump_ui_hierarchy(device_id)
            if not xml_content:
                break

            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)

            def parse_bounds(bounds_str: str) -> Optional[tuple[int, int, int, int]]:
                m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                if len(m) == 2:
                    x1, y1 = int(m[0][0]), int(m[0][1])
                    x2, y2 = int(m[1][0]), int(m[1][1])
                    if (x2 - x1) > 10 and (y2 - y1) > 10 and (x2 > 0 or y2 > 0):
                        return (x1, y1, x2, y2)
                return None

            # 1. Identify section headers to isolate Find Friends / Quick Add
            added_me_y_range = None
            find_friends_y = 0
            invite_y = 99999

            section_titles = []
            for node in root.iter("node"):
                res_id = (node.attrib.get("resource-id") or "").lower()
                txt = (node.attrib.get("text") or "").strip().lower()
                desc = (node.attrib.get("content-desc") or "").strip().lower()

                if "section-title" in res_id or "section_title" in res_id or "sectiontitle" in res_id:
                    b = parse_bounds(node.attrib.get("bounds", ""))
                    if b:
                        section_titles.append({"txt": txt or desc, "bounds": b, "y": b[1]})

            section_titles.sort(key=lambda x: x["y"])

            for i, sec in enumerate(section_titles):
                t = sec["txt"]
                if "added me" in t:
                    next_y = section_titles[i + 1]["y"] if i + 1 < len(section_titles) else sec["bounds"][3] + 600
                    added_me_y_range = (sec["y"], next_y)
                elif any(k in t for k in ["find friends", "quick add", "suggestions", "people you may know"]):
                    find_friends_y = sec["y"]
                elif "invite" in t:
                    invite_y = min(invite_y, sec["y"])

            # 2. Extract valid Quick Add candidates
            buttons = []

            # Approach A: Find structured friend cells (scu_search_friend_cell or user-result-cell)
            cells = []
            for node in root.iter("node"):
                res_id = (node.attrib.get("resource-id") or "").lower()
                if any(k in res_id for k in ["scu_search_friend_cell", "user-result-cell", "friend_cell", "friend-cell"]):
                    cells.append(node)

            for cell in cells:
                b_cell = parse_bounds(cell.attrib.get("bounds", ""))
                if not b_cell:
                    continue

                cy = (b_cell[1] + b_cell[3]) // 2

                # Exclude any cell within the "Added Me" section
                if added_me_y_range and (added_me_y_range[0] <= cy <= added_me_y_range[1]):
                    continue
                # Exclude any cell above "Find Friends" / "Quick Add"
                if find_friends_y > 0 and b_cell[3] <= find_friends_y:
                    continue
                # Exclude "Invite To Snapchat" section
                if cy >= invite_y:
                    continue

                c_name = ""
                add_btn = None

                for child in cell.iter("node"):
                    c_res = (child.attrib.get("resource-id") or "").lower()
                    c_txt = (child.attrib.get("text") or "").strip()
                    c_desc = (child.attrib.get("content-desc") or "").strip()
                    b_child = parse_bounds(child.attrib.get("bounds", ""))

                    if "result-title" in c_res:
                        c_name = c_txt or c_desc

                    desc_lower = c_desc.lower()
                    txt_lower = c_txt.lower()

                    is_add_text = desc_lower in ["add", "+ add", "add friend"] or txt_lower in ["add", "+ add", "add friend"]
                    is_invalid = any(k in desc_lower or k in txt_lower for k in ["invite", "accept", "camera", "snap", "hide", "dismiss", "contact", "contacts", "all contacts"])

                    if is_add_text and not is_invalid:
                        if b_child and b_child[1] >= 390:
                            cx = (b_child[0] + b_child[2]) // 2
                            cy_child = (b_child[1] + b_child[3]) // 2
                            add_btn = {"center": (cx, cy_child), "bounds": b_child, "name": c_name}

                if add_btn:
                    buttons.append(add_btn)

            # Approach B: Fallback to flat button scan if no structured cells matched
            if not buttons:
                for node in root.iter("node"):
                    b = parse_bounds(node.attrib.get("bounds", ""))
                    if not b:
                        continue

                    cy = (b[1] + b[3]) // 2
                    if added_me_y_range and (added_me_y_range[0] <= cy <= added_me_y_range[1]):
                        continue
                    if find_friends_y > 0 and b[3] <= find_friends_y:
                        continue
                    if cy >= invite_y or b[1] < 300:
                        continue

                    desc_lower = (node.attrib.get("content-desc") or "").strip().lower()
                    txt_lower = (node.attrib.get("text") or "").strip().lower()

                    is_add_text = desc_lower in ["add", "+ add", "add friend"] or txt_lower in ["add", "+ add", "add friend"]
                    is_invalid = any(k in desc_lower or k in txt_lower for k in ["invite", "accept", "camera", "snap", "hide", "dismiss", "contact", "contacts", "all contacts"])

                    if is_add_text and not is_invalid:
                        cx = (b[0] + b[2]) // 2
                        buttons.append({"center": (cx, cy), "bounds": b, "name": "Suggested Friend"})

            # If no buttons on current viewport, scroll down gently to reveal suggestions
            if not buttons:
                self.scroll_down(device_id, distance=450)
                time.sleep(1.2)
                continue

            for btn in buttons:
                if len(added_names) >= max_count:
                    break
                self.input_tap_human(device_id, btn["center"][0], btn["center"][1], bounds=btn["bounds"])
                display = btn.get("name") or f"Suggestion #{len(added_names) + 1}"
                added_names.append(display)
                time.sleep(random.uniform(1.8, 3.0))

            if len(added_names) < max_count:
                self.scroll_down(device_id, distance=450)
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
            or self.find_element(device_id, content_desc="Camera Capture")
        )
        if not elem:
            # Re-ensure camera landing before tapping to prevent clicking inside chat feed
            self.ensure_landing_or_search(device_id)
            elem = (
                self.find_element(device_id, resource_id="camera_capture_button")
                or self.find_element(device_id, content_desc="Take a Snap")
                or self.find_element(device_id, content_desc="Camera Capture")
            )

        coords = elem["center"] if elem else (360, 1344)
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



    def select_shortcut_and_send(self, device_id: str, shortcut_emoji: str) -> int:
        """
        Locates the user's custom shortcut tab by emoji on the Send To screen horizontal pill bar,
        taps the shortcut tab, taps its top-right 'Select All Button' to select all friends in the shortcut,
        and dispatches the Snap with the Send button.
        """
        import xml.etree.ElementTree as ET
        self.dismiss_popups(device_id)
        time.sleep(0.4)

        def parse_bounds(bounds_str: str):
            m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(m) == 2:
                return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
            return None

        clean_target = (shortcut_emoji or "").strip()
        clean_target_core = re.sub(r"[\U0001F3FB-\U0001F3FF\uFE00-\uFE0F]", "", clean_target)

        def find_shortcut_in_xml(xml_str: Optional[str]):
            if not xml_str:
                return None
            try:
                root_el = ET.fromstring(xml_str)
            except Exception:
                return None
            for node in root_el.iter():
                t = (node.attrib.get("text") or "").strip()
                d = (node.attrib.get("content-desc") or "").strip()
                b_str = node.attrib.get("bounds", "")
                b = parse_bounds(b_str)
                if not b:
                    continue
                # Tab bar is between Y 170 and 300
                if not (170 <= b[1] <= 300):
                    continue

                clean_t = re.sub(r"[🏻-🏿︀-️]", "", t)
                clean_d = re.sub(r"[🏻-🏿︀-️]", "", d)

                if (clean_target in t or clean_target in d or 
                    (clean_target_core and (clean_target_core in clean_t or clean_target_core in clean_d))):
                    return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
            return None

        # 1. Dump UI hierarchy to locate shortcut emoji tab in the horizontal bar
        xml_content = self.dump_ui_hierarchy(device_id)
        shortcut_coords = find_shortcut_in_xml(xml_content)

        # 2. If not visible in current viewport, swipe the horizontal tab bar left to reveal off-screen shortcuts
        if not shortcut_coords:
            self._run_cmd([self.adb_path, "-s", device_id, "shell", "input", "swipe", "550", "236", "180", "236", "280"], timeout=3)
            time.sleep(0.8)
            xml_scrolled = self.dump_ui_hierarchy(device_id)
            shortcut_coords = find_shortcut_in_xml(xml_scrolled)

        # 3. Resilient Fallback: If shortcut emoji still does not exist on phone
        if not shortcut_coords:
            # Rather than clicking random coordinates or failing, safely fallback to 🔥 Streak Friends!
            return self.select_recipients_and_send(device_id, select_all=False, max_recipients=5, recipient_mode="count")

        # 2. Tap shortcut tab
        self.input_tap_human(device_id, shortcut_coords[0], shortcut_coords[1])
        time.sleep(1.2)

        # 3. Locate shortcut's Select All Button
        xml_shortcut = self.dump_ui_hierarchy(device_id)
        select_all_coords = None

        if xml_shortcut:
            root = ET.fromstring(xml_shortcut)
            for node in root.iter():
                d = (node.attrib.get("content-desc") or "").lower()
                t = (node.attrib.get("text") or "").lower()
                b_str = node.attrib.get("bounds", "")
                b = parse_bounds(b_str)
                if not b:
                    continue

                if "select all" in d or "select all" in t:
                    select_all_coords = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                    break

        if not select_all_coords:
            # Fallback coordinate for Select All inside shortcut list on Infinix: (598, 523)
            select_all_coords = (598, 523)

        # 4. Tap Select All inside shortcut
        self.input_tap_human(device_id, select_all_coords[0], select_all_coords[1])
        time.sleep(0.8)

        # 5. Dismiss any popup
        self.dismiss_popups(device_id)

        # 6. Tap Send Button
        send_elem = (
            self.find_element(device_id, resource_id="send_to_send_button")
            or self.find_element(device_id, resource_id="send_button")
            or self.find_element(device_id, content_desc="Send")
        )
        send_coords = send_elem["center"] if send_elem else (663, 1553)
        bounds = send_elem["bounds"] if send_elem else (623, 1540, 704, 1567)
        self.input_tap_human(device_id, send_coords[0], send_coords[1], bounds=bounds)
        time.sleep(2.5)

        if self.detect_screen_state(device_id) == "SEND_TO":
            self.input_tap(device_id, 663, 1553)
            time.sleep(1.5)

        return 1

    def select_all_and_send(self, device_id: str) -> int:
        """
        Locates the global 'Select All Button' on the main Send To screen,
        taps it to select all friends, and dispatches the Snap with the Send button.
        """
        import xml.etree.ElementTree as ET
        self.dismiss_popups(device_id)
        time.sleep(0.4)

        def parse_bounds(bounds_str: str):
            m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(m) == 2:
                return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
            return None

        xml_content = self.dump_ui_hierarchy(device_id)
        select_all_coords = None

        if xml_content:
            root = ET.fromstring(xml_content)
            for node in root.iter():
                d = (node.attrib.get("content-desc") or "").lower()
                t = (node.attrib.get("text") or "").lower()
                b_str = node.attrib.get("bounds", "")
                b = parse_bounds(b_str)
                if not b:
                    continue

                if "select all" in d or "select all" in t:
                    select_all_coords = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                    break

        if not select_all_coords:
            # Fallback coordinate for global Select All on Infinix: (598, 713)
            select_all_coords = (598, 713)

        self.input_tap_human(device_id, select_all_coords[0], select_all_coords[1])
        time.sleep(0.8)

        self.dismiss_popups(device_id)

        send_elem = (
            self.find_element(device_id, resource_id="send_to_send_button")
            or self.find_element(device_id, resource_id="send_button")
            or self.find_element(device_id, content_desc="Send")
        )
        send_coords = send_elem["center"] if send_elem else (663, 1553)
        bounds = send_elem["bounds"] if send_elem else (623, 1540, 704, 1567)
        self.input_tap_human(device_id, send_coords[0], send_coords[1], bounds=bounds)
        time.sleep(2.5)

        if self.detect_screen_state(device_id) == "SEND_TO":
            self.input_tap(device_id, 663, 1553)
            time.sleep(1.5)

        return 1

    def select_recipients_and_send(
        self,
        device_id: str,
        select_all: bool = False,
        max_recipients: int = 5,
        recipient_mode: str = "count",
        shortcut_emoji: Optional[str] = None
    ) -> int:
        """
        Selects recipients on Send To screen and dispatches the Snap.
        Supports:
        - 'shortcut': Taps custom emoji shortcut and its Select All button.
        - 'select_all': Taps global Select All button.
        - 'count': Strictly selects top N friends from Best Friends & Recents.
        """
        if recipient_mode == "shortcut" and shortcut_emoji:
            return self.select_shortcut_and_send(device_id, shortcut_emoji)

        if recipient_mode == "select_all" or (select_all and (max_recipients is None or max_recipients >= 999)):
            return self.select_all_and_send(device_id)
        """
        Selects recipients on Send To screen and dispatches the Snap.
        Strictly selects friends from 'Best Friends' and 'Recents & Suggested' sections.
        Guarantees ZERO interaction with 'Find Friends', 'Quick Add', 'Stories' (My Story), or 'My AI'.
        Dynamically adjusts for screen movement when recipient confirmation bar appears.
        """
        # Dismiss any modal dialog (e.g. Add to Story or Public Story)
        self.dismiss_popups(device_id)
        time.sleep(0.4)

        import xml.etree.ElementTree as ET

        def parse_bounds(bounds_str: str):
            m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
            if len(m) == 2:
                return int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1])
            return None

        ignore_exact = {
            "send to?", "send to", "all", "new friends", "new", "post to...",
            "best friends", "recents & suggested", "recents", "recent",
            "find friends", "my ai", "last snap", "my story", "stories",
            "just for friends", "friends, followers, and everyone",
            "recently joined", "in my contacts", "ok", "cancel", "send"
        }

        def extract_available_recipients(xml_text: str):
            """Parses Send To UI hierarchy and returns valid friends within Best Friends and Recents"""
            if not xml_text:
                return [], 1500
            try:
                root = ET.fromstring(xml_text)
            except Exception:
                return [], 1500

            best_friends_y = None
            recents_y = None
            find_friends_y = None

            # Collect active streak indicators (🔥 badge nodes or streak text)
            streak_ys = []
            for node in root.iter("node"):
                t = (node.attrib.get("text") or "").strip()
                t_low = t.lower()
                d = (node.attrib.get("content-desc") or "").strip()
                d_low = d.lower()
                b = parse_bounds(node.attrib.get("bounds", ""))
                if not b:
                    continue

                is_streak_badge = (
                    "🔥" in t or "🔥" in d
                    or (len(t) <= 12 and "streak" in t_low)
                    or (len(d) <= 12 and "streak" in d_low)
                )
                if is_streak_badge:
                    streak_ys.append((b[1] + b[3]) // 2)

                if "best friends" in t_low and best_friends_y is None:
                    best_friends_y = b[1]
                elif ("recents" in t_low or "recent" in t_low) and recents_y is None:
                    recents_y = b[1]
                elif ("find friends" in t_low or "quick add" in t_low or "add friends" in t_low) and find_friends_y is None:
                    find_friends_y = b[1]

            if not best_friends_y:
                best_friends_y = 250
            if not recents_y:
                recents_y = best_friends_y + 180
            if not find_friends_y:
                find_friends_y = 1500

            candidates = []
            seen = set()

            for node in root.iter("node"):
                raw_t = (node.attrib.get("text") or "").strip()
                t_lower = raw_t.lower()
                b = parse_bounds(node.attrib.get("bounds", ""))
                if not b or not raw_t:
                    continue

                # STRICT BOUNDS: strictly between best_friends_y and find_friends_y
                if b[1] < best_friends_y or b[3] > find_friends_y:
                    continue

                if t_lower in ignore_exact:
                    continue
                if any(t_lower.startswith(prefix) for prefix in ["post to", "add a snap", "my story", "friends, followers"]):
                    continue

                # Friends row name bounds (x=100..600, b[0] <= 220, height 20..80)
                height = b[3] - b[1]
                if b[0] >= 100 and b[0] <= 220 and b[2] <= 620 and 20 <= height <= 80:
                    if any(char in raw_t for char in ["🔥", "✨"]) and len(raw_t) <= 5:
                        continue
                    if "ago" in t_lower or len(raw_t) > 35 or "," in raw_t or "+" in raw_t or "and others" in t_lower:
                        continue

                    # Support international/Urdu characters by stripping whitespace rather than discarding unicode
                    clean_key = raw_t.strip().lower()
                    if not clean_key or clean_key in seen:
                        continue
                    seen.add(clean_key)

                    row_y = (b[1] + b[3]) // 2
                    has_streak = any(abs(row_y - sy) <= 35 for sy in streak_ys) or ("🔥" in raw_t)

                    candidates.append({
                        "name": raw_t,
                        "clean_key": clean_key,
                        "coords": (633, row_y),
                        "bounds": b,
                        "has_streak": has_streak
                    })

            # If candidates with active streaks (🔥) exist on screen, strictly select streak friends
            streak_candidates = [c for c in candidates if c["has_streak"]]
            if streak_candidates:
                candidates = streak_candidates
            else:
                candidates.sort(key=lambda c: c["coords"][1])

            return candidates, find_friends_y

        selected_count = 0
        selected_keys = set()
        # Strictly enforce user's selected recipient count. select_all only overrides when count is unlimited (>= 999)
        if select_all and (max_recipients is None or max_recipients <= 0 or max_recipients >= 999):
            max_to_select = 999
        else:
            max_to_select = max_recipients if (max_recipients and max_recipients > 0) else 5

        # Dynamic selection loop: re-reads screen position after selection shifts the list
        for attempt in range(max_to_select):
            xml_content = self.dump_ui_hierarchy(device_id)
            if not xml_content:
                break

            candidates, upper_cutoff = extract_available_recipients(xml_content)
            # Find next candidate that has not been selected yet
            next_friend = None
            for cand in candidates:
                if cand["clean_key"] not in selected_keys:
                    next_friend = cand
                    break

            if not next_friend:
                break

            # Strictly ensure coordinate is above Find Friends cutoff
            tap_x, tap_y = next_friend["coords"]
            if tap_y >= upper_cutoff:
                break

            self.input_tap_human(device_id, tap_x, tap_y)
            selected_keys.add(next_friend["clean_key"])
            selected_count += 1
            time.sleep(random.uniform(0.35, 0.6))

            if selected_count >= max_to_select:
                break

        # Safety Fallback: if dynamic selection couldn't read any candidates (e.g. non-standard XML dump)
        if selected_count == 0:
            # Verified safe coordinates on Infinix device strictly inside Best Friends & Recents (above 1400)
            fallback_coords = [(633, 814), (633, 1262), (633, 1362)]
            limit = min(max_to_select, len(fallback_coords))
            for circle in fallback_coords[:limit]:
                self.input_tap_human(device_id, circle[0], circle[1])
                selected_count += 1
                time.sleep(random.uniform(0.3, 0.5))

        time.sleep(0.6)  # Human hesitation before pressing Send

        # Dismiss any unexpected story confirmation modal if triggered
        self.dismiss_popups(device_id)

        # Tap Send button (bottom right blue circular button with paper plane at bounds [623,1540][704,1567])
        send_elem = (
            self.find_element(device_id, resource_id="send_to_send_button")
            or self.find_element(device_id, resource_id="send_button")
            or self.find_element(device_id, content_desc="Send")
        )
        send_coords = send_elem["center"] if send_elem else (663, 1553)
        bounds = send_elem["bounds"] if send_elem else (623, 1540, 704, 1567)
        self.input_tap_human(device_id, send_coords[0], send_coords[1], bounds=bounds)
        time.sleep(2.5)  # Wait for snap dispatch

        # Verify dispatch completed: if Send To screen still active, tap send_coords again
        state_after = self.detect_screen_state(device_id)
        if state_after == "SEND_TO":
            self.input_tap(device_id, 663, 1553)
            time.sleep(2.0)

        # Cleanly ensure camera landing
        self.ensure_camera_landing(device_id)
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

            # Strictly exclude group chats (Snapchat group names contain commas or exceed 35 chars)
            if "," in friend_name or len(friend_name) > 35:
                continue

            joined_row = " ".join(row_texts).lower()

            # Strictly exclude group activity markers and non-friend cards (feed_cross_button / ad / contact invites)
            if any(marker in joined_row for marker in ["received from", "opened by", "sent to", "sent by", "feed_cross_button"]):
                continue

            clean_digits = re.sub(r"[\s\-\+\(\)]", "", friend_name)
            if clean_digits.isdigit() and len(clean_digits) >= 7:
                continue
            has_streak = ("🔥" in joined_row or "streak" in joined_row)

            def get_inactivity_days(txt: str) -> Optional[int]:
                m_days = re.search(r'(\d+)\s*d(?:ays?)?(?:\s*ago)?\b', txt)
                if m_days:
                    return int(m_days.group(1))
                m_weeks = re.search(r'(\d+)\s*w(?:eeks?)?(?:\s*ago)?\b', txt)
                if m_weeks:
                    return int(m_weeks.group(1)) * 7
                m_months = re.search(r'(\d+)\s*mo(?:nths?)?(?:\s*ago)?\b', txt)
                if m_months:
                    return int(m_months.group(1)) * 30
                m_years = re.search(r'(\d+)\s*y(?:ears?)?(?:\s*ago)?\b', txt)
                if m_years:
                    return int(m_years.group(1)) * 365
                if any(k in txt for k in ["months ago", "month ago"]):
                    return 30
                if any(k in txt for k in ["weeks ago", "week ago"]):
                    return 14
                return None

            dormant_days = get_inactivity_days(joined_row)
            threshold = days_threshold if (days_threshold and days_threshold > 0) else 14
            is_inactive = (dormant_days is not None and dormant_days >= threshold)

            matches = False
            reason = ""
            if filter_type == "no_streak" and not has_streak:
                matches = True
                reason = "No active streak emoji (🔥) found"
            elif filter_type == "inactive" and is_inactive:
                matches = True
                reason = f"Dormant timestamp detected (~{dormant_days}d inactive, exceeds {threshold}d limit)"
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

    def find_remove_confirmation_button(self, device_id: str) -> Optional[dict]:
        """
        Dynamically locates the 'Remove' confirmation button inside Snapchat's 'Remove Friend' dialog.
        Handles:
        1. Explicit text or content-desc == 'Remove' (or known standard button ids).
        2. Unlabeled / custom-drawn View inside com.snapchat.android:id/dialog_content (directly above cancel_button).
        3. Relative geometry match above cancel_button.
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
                    return (int(m[0][0]), int(m[0][1]), int(m[1][0]), int(m[1][1]))
                return None

            # 1. Direct match: explicit text or content-desc == 'Remove'
            for node in root.iter("node"):
                txt = (node.attrib.get("text") or "").strip().lower()
                desc = (node.attrib.get("content-desc") or "").strip().lower()
                res = (node.attrib.get("resource-id") or "").strip().lower()
                b = parse_bounds(node.attrib.get("bounds", ""))
                if b and (txt == "remove" or desc == "remove" or "remove_button" in res or res.endswith("button1")):
                    center = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                    return {"center": center, "bounds": b, "text": "Remove"}

            # 2. Inspect dialog_content container for clickable action sibling (above cancel_button)
            for node in root.iter("node"):
                res = (node.attrib.get("resource-id") or "").lower()
                if "dialog_content" in res:
                    for child in node.findall("node"):
                        c_res = (child.attrib.get("resource-id") or "").lower()
                        c_txt = (child.attrib.get("text") or "").strip().lower()
                        c_click = child.attrib.get("clickable", "false").lower() == "true"
                        c_bounds = parse_bounds(child.attrib.get("bounds", ""))
                        if c_click and c_bounds:
                            if "cancel" not in c_res and c_txt != "cancel" and "title" not in c_res:
                                center = ((c_bounds[0] + c_bounds[2]) // 2, (c_bounds[1] + c_bounds[3]) // 2)
                                return {"center": center, "bounds": c_bounds, "text": "Remove"}

            # 3. Positional match relative to cancel_button
            cancel_b = None
            for node in root.iter("node"):
                res = (node.attrib.get("resource-id") or "").lower()
                txt = (node.attrib.get("text") or "").strip().lower()
                if "cancel_button" in res or txt == "cancel":
                    b = parse_bounds(node.attrib.get("bounds", ""))
                    if b:
                        cancel_b = b
                        break

            if cancel_b:
                for node in root.iter("node"):
                    b = parse_bounds(node.attrib.get("bounds", ""))
                    if b and node.attrib.get("clickable", "false").lower() == "true":
                        if b != cancel_b and b[3] <= cancel_b[1] + 15 and b[1] >= cancel_b[1] - 250:
                            center = ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)
                            return {"center": center, "bounds": b, "text": "Remove"}
        except Exception:
            pass

        return None

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
                # Target is not a friend (e.g. group chat or ad). Safely dismiss popup menu without blind taps!
                self.input_key(device_id, 4)
                time.sleep(0.8)
                return False
            time.sleep(1.2)

            # 3. Tap 'Remove Friend'
            remove_elem = self.find_element(device_id, text="Remove Friend")
            if remove_elem:
                self.input_tap_human(device_id, remove_elem["center"][0], remove_elem["center"][1], bounds=remove_elem.get("bounds"))
            else:
                # Sub-menu did not contain 'Remove Friend'. Safely press Back twice to return to feed.
                self.input_key(device_id, 4)
                time.sleep(0.5)
                self.input_key(device_id, 4)
                time.sleep(0.8)
                return False
            time.sleep(1.2)

            # 4. Tap 'Remove' in confirmation modal
            confirm_elem = None
            for _ in range(2):
                confirm_elem = self.find_remove_confirmation_button(device_id)
                if confirm_elem:
                    break
                time.sleep(0.6)

            if confirm_elem:
                self.input_tap_human(device_id, confirm_elem["center"][0], confirm_elem["center"][1], bounds=confirm_elem.get("bounds"))
                time.sleep(1.5)
                return True
            else:
                self.input_key(device_id, 4)
                time.sleep(0.8)
                return False
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

