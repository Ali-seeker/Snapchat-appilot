# Day 1: Manual Test Plan & Step-by-Step Test Cases
**Project:** Appilot Snapchat Companion  
**Goal:** Verify all Day 1 features, UI responsiveness, WebSocket synchronization, safety controls, and edge cases manually.

---

## Pre-requisites: Services Running
Ensure both services are running in your terminals:
1. **Backend Server:** `http://localhost:8000` (Running via `start_backend.bat`)
2. **Frontend Dashboard:** `http://localhost:5173` (Running via `start_frontend.bat`)

---

## Test Cases Matrix

### TC-01: Backend REST API & Swagger Health
* **Action:** Open your browser and navigate to: `http://localhost:8000/docs`
* **Expected Result:**
  * FastAPI Swagger interactive documentation loads.
  * Try executing `GET /api/status`: Returns `200 OK` with JSON `{ "state": "IDLE", ... }`.
  * Try executing `GET /api/contacts`: Returns `200 OK` with initial demo contacts list.
* **Pass / Fail:** [ ]

---

### TC-02: React Frontend Dashboard Live WebSocket Link
* **Action:** Open `http://localhost:5173` in your browser.
* **Expected Result:**
  * Top navigation header loads with project title: **Appilot Companion**.
  * Current state badge displays **`IDLE`** (grey pill).
  * WebSocket health indicator shows **`WS Active (X ms)`** with a green pulse icon.
* **Pass / Fail:** [ ]

---

### TC-03: Setup & Transparency Disclosure Guard (FR-01)
* **Action:**
  1. Observe the **FR-01: Setup & Transparency Disclosure** panel at the top.
  2. Leave the checkbox *"I acknowledge the assisted nature..."* **unchecked**.
  3. Select any contact from the target list below and click the **Review & Start** button.
* **Expected Result:**
  * An alert appears: *"Please acknowledge the Setup & Transparency Disclosure first (FR-01)."*
  * Workflow does NOT start without user acknowledgement.
  * Check the checkbox: The panel displays a green *"Acknowledged"* badge.
* **Pass / Fail:** [ ]

---

### TC-04: User-Curated Target List Management (FR-04)
* **Action:**
  1. In the **FR-04: User-Curated Target List** panel, type a new username: `  MyNewFriend_99  ` (with spaces) and Display Name: `Test Friend`.
  2. Click **Add**.
  3. Try adding the exact same username again: `mynewfriend_99`.
  4. Type a short username `ab` and click **Add**.
* **Expected Result:**
  * Contact is added with username normalized to lowercase and trimmed: `@mynewfriend_99`.
  * Duplicate attempt shows red error banner: *"Target 'mynewfriend_99' already exists in list (duplicate rejected)"*.
  * Short username shows validation error: *"Username must be at least 3 characters"*.
  * Search filter works in real-time when typing in search box.
* **Pass / Fail:** [ ]

---

### TC-05: Pre-Execution Safety Review Modal (FR-05)
* **Action:**
  1. Select 2 contacts by checking their boxes in the target list table.
  2. Click **Review & Start (2)**.
* **Expected Result:**
  * Modal dialog opens: *"Confirm Consequential Action"*.
  * Displays exact target recipient count: `Target Recipients (2)`.
  * Lists both selected usernames with blue bullet points.
  * Click **Cancel** -> Modal closes without state change.
  * Click **Confirm & Proceed** -> Modal closes and workflow begins.
* **Pass / Fail:** [ ]

---

### TC-06: Start, Pause, Resume & Emergency STOP (FR-03)
* **Action:**
  1. Start a workflow or click **Run Full Test Suite** in Demo Mode.
  2. While the workflow is running (state badge turns green `RUNNING`), click **Pause**.
  3. Verify state badge changes to yellow `PAUSED`.
  4. Click **Resume** -> State returns to green `RUNNING`.
  5. Click the big red **EMERGENCY STOP** button.
* **Expected Result:**
  * Execution halts immediately.
  * State badge instantly turns red **`STOPPED`**.
  * Real-time audit log records: `[System] Emergency stop executed: User requested stop` with status `CANCELLED` and reason `USER_EMERGENCY_STOP`.
  * Click **Reset** button in header to return state back to `IDLE`.
* **Pass / Fail:** [ ]

---

### TC-07: Deterministic Demo Mode Test Bench (FR-12)
* **Action:**
  In the **FR-12: Deterministic Demo Mode** section, test the following buttons:
  1. Click **Test Success Flow**: Simulates target review and safe local reminder preparation.
  2. Click **Test Duplicate Rejection**: Automatically verifies duplicate injection rejection.
  3. Click **Test Inactivity Policy**: Verifies unverified last-active data is marked strictly as `UNKNOWN`, never guessing inactive.
  4. Click **Test Error & Recovery**: Simulates timeout error and verifies system recovers cleanly to `NEEDS_USER_ACTION`.
* **Expected Result:**
  * Each scenario streams distinct events into the live log with appropriate colored badges (`COMPLETED`, `SKIPPED`, `UNKNOWN`, `FAILED`).
* **Pass / Fail:** [ ]

---

### TC-08: Live Audit Log & Telemetry (FR-09 & FR-10)
* **Action:**
  1. Observe the **FR-09 & FR-10: Live Telemetry & Audit Log** panel.
  2. Check that each event has: Local Timestamp, Color-coded status tag, Workflow name in brackets, and Reason Code.
  3. Click the **Trash / Clear** icon.
* **Expected Result:**
  * Audit logs update in real-time over WebSocket without page refresh.
  * Trash button clears the log stream.
* **Pass / Fail:** [ ]

---

### TC-09: Android Debug APK Verification (SC-01 & SC-02)
* **File Location:** `android/app/build/outputs/apk/debug/app-debug.apk` (5.78 MB).
* **Action (If Android Device/Emulator is available):**
  1. Connect device or start emulator.
  2. Run:
     ```powershell
     adb install -r android\app\build\outputs\apk\debug\app-debug.apk
     adb reverse tcp:8000 tcp:8000
     ```
  3. Open **Appilot Companion** on the device.
* **Expected Result:**
  * Native app launches with dark UI, Setup Disclosure text, Accessibility Service toggle, and Emergency STOP button.
  * Tapping "Grant Accessibility Permission" opens Android Accessibility settings.
  * Tapping Emergency STOP on device triggers stop event across WebSocket to backend and dashboard.
* **Pass / Fail:** [ ]
