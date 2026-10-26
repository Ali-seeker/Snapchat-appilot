from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONTACTS_FILE = DATA_DIR / "contacts.json"
AUDIT_LOG_FILE = DATA_DIR / "audit_logs.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
