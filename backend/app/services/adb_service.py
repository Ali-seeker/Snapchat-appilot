import subprocess
import shutil
import re
from typing import List, Dict, Optional
from ..models.schemas import DeviceInfo

class ADBService:
    def __init__(self):
        self.adb_path = shutil.which("adb") or "adb"

    def is_adb_available(self) -> bool:
        try:
            res = subprocess.run([self.adb_path, "version"], capture_output=True, text=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    def list_devices(self) -> List[DeviceInfo]:
        devices: List[DeviceInfo] = []
        if not self.is_adb_available():
            return devices

        try:
            res = subprocess.run([self.adb_path, "devices", "-l"], capture_output=True, text=True, timeout=5)
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
            res = subprocess.run(
                [self.adb_path, "-s", device_id, "reverse", f"tcp:{port}", f"tcp:{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_battery(self, device_id: str) -> Optional[int]:
        try:
            res = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "dumpsys", "battery"],
                capture_output=True,
                text=True,
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
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
            return res.returncode == 0
        except Exception:
            return False

    def stop_snapchat(self, device_id: str) -> bool:
        """Force stops Snapchat"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "am", "force-stop", "com.snapchat.android"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def is_snapchat_running(self, device_id: str) -> bool:
        """Checks if Snapchat is currently visible in foreground"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "dumpsys", "window"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return "com.snapchat.android" in res.stdout
        except Exception:
            return False

    def input_tap(self, device_id: str, x: int, y: int) -> bool:
        """Executes hardware tap via adb input"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "tap", str(x), str(y)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def input_text(self, device_id: str, text: str) -> bool:
        """Types text via adb input text, escaping whitespace and shell characters"""
        try:
            # Replace spaces with %s for adb shell input text
            safe_text = text.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'")
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "text", safe_text]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def input_key(self, device_id: str, keycode: int) -> bool:
        """Sends keyevent: 66=Enter, 4=Back, 3=Home, 67=Backspace"""
        try:
            cmd = [self.adb_path, "-s", device_id, "shell", "input", "keyevent", str(keycode)]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def dump_ui_hierarchy(self, device_id: str) -> Optional[str]:
        """Dumps UI XML hierarchy from device screen and returns as string"""
        try:
            subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"],
                capture_output=True,
                text=True,
                timeout=8
            )
            res = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "cat", "/sdcard/window_dump.xml"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass
        return None

    def find_bounds(self, device_id: str, query: str) -> Optional[tuple[int, int]]:
        """Parses UI XML hierarchy to find center (x, y) coordinates for target text or id"""
        xml_content = self.dump_ui_hierarchy(device_id)
        if not xml_content:
            return None

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            q_lower = query.lower()

            for node in root.iter("node"):
                text = (node.attrib.get("text") or "").lower()
                desc = (node.attrib.get("content-desc") or "").lower()
                res_id = (node.attrib.get("resource-id") or "").lower()

                if q_lower in text or q_lower in desc or q_lower in res_id:
                    bounds_str = node.attrib.get("bounds", "")
                    # Format: [x1,y1][x2,y2]
                    m = re.findall(r"\[(\d+),(\d+)\]", bounds_str)
                    if len(m) == 2:
                        x1, y1 = int(m[0][0]), int(m[0][1])
                        x2, y2 = int(m[1][0]), int(m[1][1])
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        return (center_x, center_y)
        except Exception:
            pass
        return None

    def take_screenshot(self, device_id: str, local_path: str) -> bool:
        """Captures device screenshot and saves locally"""
        try:
            subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"],
                capture_output=True,
                timeout=8
            )
            res = subprocess.run(
                [self.adb_path, "-s", device_id, "pull", "/sdcard/screen.png", local_path],
                capture_output=True,
                timeout=8
            )
            return res.returncode == 0
        except Exception:
            return False

adb_service = ADBService()

