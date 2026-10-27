import sys
import time
import json
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def get_status():
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/status") as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def get_latest_logs(limit=15):
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/logs?limit={limit}") as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        return []

def trigger_workflow(endpoint, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode('utf-8'))

def monitor_until_complete(timeout=90):
    print("[-] Monitoring workflow execution...")
    start = time.time()
    seen_ids = set()
    
    while time.time() - start < timeout:
        status = get_status()
        current_state = status.get("state")
        workflow = status.get("workflow")
        
        # Print new logs
        logs = get_latest_logs(10)
        for log in reversed(logs):
            lid = f"{log.get('timestamp')}_{log.get('message')}"
            if lid not in seen_ids:
                seen_ids.add(lid)
                print(f"[{log.get('result')}] {log.get('workflow')}: {log.get('message')}")
        
        if current_state in ["COMPLETED", "FAILED", "STOPPED", "IDLE"]:
            if current_state == "COMPLETED":
                print(f"[+] Workflow '{workflow}' reached COMPLETED state successfully!")
                return True
            elif current_state == "FAILED":
                print(f"[!] Workflow '{workflow}' FAILED!")
                return False
            elif current_state == "STOPPED":
                print(f"[!] Workflow '{workflow}' STOPPED!")
                return False
                
        time.sleep(1.5)
        
    print("[!] Workflow timed out!")
    return False

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "follow"
    print(f"=== Starting Live Real-Time Test: {action} ===")
    
    if action == "follow":
        res = trigger_workflow("/api/workflow/follow", {
            "mode": "quick_add",
            "max_count": 2,
            "device_id": "08265372BO000706"
        })
        print("API Response:", res)
        success = monitor_until_complete(timeout=60)
        sys.exit(0 if success else 1)

    elif action == "snap":
        res = trigger_workflow("/api/workflow/snap", {
            "random_filter": True,
            "select_all": True,
            "max_recipients": 5,
            "device_id": "08265372BO000706"
        })
        print("API Response:", res)
        success = monitor_until_complete(timeout=90)
        sys.exit(0 if success else 1)

    elif action == "snapscore":
        res = trigger_workflow("/api/workflow/snapscore", {
            "cycles": 2,
            "select_all": True,
            "max_recipients": 5,
            "cooldown_seconds": 10,
            "device_id": "08265372BO000706"
        })
        print("API Response:", res)
        success = monitor_until_complete(timeout=180)
        sys.exit(0 if success else 1)

    elif action == "unfollow":
        res = trigger_workflow("/api/workflow/unfollow", {
            "filter_type": "no_streak",
            "days_threshold": 17,
            "max_unfollow": 1,
            "device_id": "08265372BO000706"
        })
        print("API Response:", res)
        success = monitor_until_complete(timeout=90)
        sys.exit(0 if success else 1)

    elif action == "chain":
        res = trigger_workflow("/api/workflow/chain", {
            "routine_type": "morning",
            "device_id": "08265372BO000706"
        })
        print("API Response:", res)
        success = monitor_until_complete(timeout=200)
        sys.exit(0 if success else 1)

