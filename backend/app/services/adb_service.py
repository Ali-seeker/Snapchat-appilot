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

adb_service = ADBService()
