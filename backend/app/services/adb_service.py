import subprocess
import shutil
import re
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
        """Launches Snapchat main activity"""
        try:
            cmd = [
                self.adb_path, "-s", device_id, "shell",
                "monkey", "-p", "com.snapchat.android", "-c", "android.intent.category.LAUNCHER", "1"
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

    def input_text(self, device_id: str, text: str) -> bool:
        """Types text via adb input text, escaping whitespace and shell characters"""
        try:
            safe_text = text.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'")
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "text", safe_text]
            res = self._run_cmd(cmd, timeout=5)
            return res.returncode == 0
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
                # Look for search-textfield first
                for node in root.iter("node"):
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    if "search-textfield" in res_id:
                        c = get_valid_center(node.attrib.get("bounds", ""))
                        if c:
                            return c
                # Look for header search icon
                for node in root.iter("node"):
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    desc = (node.attrib.get("content-desc") or "").lower()
                    if "hova_header_search_icon" in res_id or "search" in desc:
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

            # 3. Specialized query: "clear"
            if q_lower in ["clear", "clear-button"]:
                for node in root.iter("node"):
                    res_id = (node.attrib.get("resource-id") or "").lower()
                    if "clear-button" in res_id or "clear_button" in res_id:
                        c = get_valid_center(node.attrib.get("bounds", ""))
                        if c:
                            return c
                # Fallback to known clear button bounds for search bar
                return (516, 132)

            # 4. General fallback search across text, content-desc, and resource-id
            for node in root.iter("node"):
                text = (node.attrib.get("text") or "").lower()
                desc = (node.attrib.get("content-desc") or "").lower()
                res_id = (node.attrib.get("resource-id") or "").lower()

                if q_lower in text or q_lower in desc or q_lower in res_id:
                    c = get_valid_center(node.attrib.get("bounds", ""))
                    if c:
                        return c
        except Exception:
            pass
        return None

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

