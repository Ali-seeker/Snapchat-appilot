# Day 2: Manual Test Plan & Step-by-Step Test Cases
**Project:** Snapchat Appilot (Day 2 Delivery Baseline)  
**Branch:** `day-2-automation`  
**Goal:** Verify all Day 2 features manually: Real Snapchat Automation on physical Infinix device, ADB + AccessibilityService synergy, Streak Reminders & Snap Draft checklist, Emergency Stop circuit breaker, and honest status telemetry.

---

## Pre-requisites & Setup
Ensure the following are ready before beginning manual testing:
1. **Device Connected:** Infinix phone (`Infinix X6817`) connected to PC via USB with USB Debugging enabled.
2. **Reverse Tunnel Active:** Port reverse verified (`adb reverse tcp:8000 tcp:8000`).
3. **Appilot Companion App:** Installed on phone with:
   - **Accessibility Service:** `Active` (Green)
   - **Backend Link:** `Connected` (Green)
4. **Backend Server:** Running on `http://localhost:8000` (via `start_backend.bat`).
5. **Frontend Dashboard:** Running on `http://localhost:5173` (via `start_frontend.bat`).

---

## Day 2 Test Cases Matrix

### TC-D2-01: Live Device Detection & Dual-Mode Toggle
* **Objective:** Verify dashboard detects connected Infinix phone and allows switching between Live Device and Simulation modes.
* **Steps:**
  1. Open Chrome/Edge and go to `http://localhost:5173` (press `Ctrl + Shift + R` for fresh reload).
  2. Look at the **Control Panel** (top right section).
* **Expected Result:**
  * Cyan pill badge is visible: **`Connected: INFINIX Infinix X6817`** (or connected phone ID).
  * Mode Switcher button is visible: Click to toggle between **`Live Device Mode`** (cyan) and **`Simulation Mode`** (grey).
  * Set it to **`Live Device Mode`**.
* **Pass / Fail:** [ ]

---

### TC-D2-02: Real Snapchat Automation — Add Friend (`testuser`)
* **Objective:** Verify end-to-end live automation opens Snapchat, searches for a real public user, taps the Add Friend button, and records success.
* **Steps:**
  1. In the **Target List**, find the contact **`testuser`** (`Snapchat Public Tester`).
  2. Check the checkbox next to `testuser`.
  3. Ensure **Setup & Transparency Disclosure** checkbox is checked.
  4. Ensure mode is **Live Device Mode**.
  5. Click **Review & Start (1)**.
  6. In the confirmation modal, verify target `@testuser` is listed, then click **Confirm & Proceed**.
  7. **Watch your Infinix mobile screen closely!**
* **Expected Result:**
  * Mobile screen does NOT open Google or random launcher apps.
  * Mobile automatically launches **Snapchat** directly onto the camera screen.
  * Search icon at top-left is tapped.
  * Search bar is cleared, and `testuser` is typed.
  * Search results load from Snapchat servers.
  * Real candidate row is identified and the **`Add`** button (`add-friend-button`) is automatically tapped.
  * Anti-ban human jitter (1.8s - 3.2s) is observed between actions.
  * Dashboard Live Execution Modal streams steps in real-time and completes with green status:  
    `Successfully sent friend request to @testuser!`
* **Pass / Fail:** [ ]

---

### TC-D2-03: Safe Non-Existent Account Handling (`sam_snap99` / Fake User)
* **Objective:** Verify the system never reports fake success when a searched account does not exist or has no Add button.
* **Steps:**
  1. In the **Target List**, add a new fake username (e.g. `nonexistent_user_9988`) or select `sam_snap99`.
  2. Select this single target and click **Review & Start (1)** -> **Confirm & Proceed**.
  3. Observe mobile screen and dashboard logs.
* **Expected Result:**
  * Snapchat opens and searches for the target.
  * Snapchat displays 0 user accounts (no Add Friend button appears).
  * System does NOT crash and does NOT claim fake success.
  * Audit log accurately records:  
    `Target @... search completed. No Add Friend button present on Snapchat for this query.` with status `FAILED` and reason `NO_ADD_BUTTON_FOUND`.
  * Search bar is safely cleared, and Snapchat returns to landing screen.
* **Pass / Fail:** [ ]

---

### TC-D2-04: Live In-Flight Emergency STOP
* **Objective:** Verify Emergency STOP halts live device automation immediately mid-execution.
* **Steps:**
  1. Select 2 contacts from the list (e.g. `testuser` and `alex.dev`).
  2. Click **Review & Start (2)** -> **Confirm & Proceed**.
  3. As soon as Snapchat opens and begins typing the first search, click the big red **EMERGENCY STOP** button on the dashboard (or the red button in the Companion app).
* **Expected Result:**
  * Automation stops instantly.
  * No further taps or text inputs occur on the phone.
  * Dashboard state changes immediately to red **`STOPPED`**.
  * Audit log records: `Emergency stop executed: User requested stop` with status `CANCELLED`.
  * Click **Reset** in the top navigation bar to return to `IDLE`.
* **Pass / Fail:** [ ]

---

### TC-D2-05: Companion Resilient Auto-Reconnect
* **Objective:** Verify the Android companion automatically recovers if the backend restarts or USB cable is replugged.
* **Steps:**
  1. Observe the **Appilot Companion** app on the phone showing `Backend Link Connected` (Green).
  2. Unplug the USB cable for 3 seconds, then plug it back in.
  3. (Or restart backend server in terminal).
  4. Wait up to 3 to 5 seconds without touching the phone.
* **Expected Result:**
  * While disconnected, status temporarily displays `Disconnected (Auto-reconnecting...)`.
  * Within 3 seconds of connection availability, companion automatically reconnects.
  * Companion status turns back to **`Backend Link Connected` (Green)** automatically.
  * Tapping on the status text also triggers manual reconnect instantly with a Toast: *"Connecting to Backend..."*.
* **Pass / Fail:** [ ]

---

### TC-D2-06: FR-07 Streak Reminders Creation & Persistence
* **Objective:** Verify creation of user-controlled streak reminders and verify they survive page reload.
* **Steps:**
  1. Scroll to the **FR-07 & FR-08: Streak Reminders & Snap Drafts** panel.
  2. In the creation form:
     - Select a recipient from dropdown: `@testuser`
     - Set time: `21:00 (Daily)`
     - Draft text: `🔥 Send evening streak snap with lens filter`
     - Click **Add**.
  3. Refresh the browser page (`Ctrl + Shift + R`).
* **Expected Result:**
  * New reminder card appears in the list with blue clock icon and `@testuser`.
  * Status badge shows yellow **`Needs user action`** (policy compliant, no autonomous sending).
  * After page reload, the reminder is still present (persisted in `backend/data/reminders.json`).
* **Pass / Fail:** [ ]

---

### TC-D2-07: FR-08 Snap Draft / Checklist Toggle & Deletion
* **Objective:** Verify streak checklist task completion toggle and deletion.
* **Steps:**
  1. In the **Streak Reminders & Snap Drafts** panel, locate the reminder created in TC-D2-06.
  2. Click the circular checkmark icon next to the reminder.
  3. Observe text and badge change.
  4. Click the checkmark icon again.
  5. Click the red **Trash** icon to delete the reminder.
* **Expected Result:**
  * When checked: text gets strikethrough, checkmark turns green, badge changes to **`Completed`** (Green).
  * When clicked again: reverts to **`Needs user action`** (Yellow).
  * When trash icon is clicked: reminder is removed immediately from list and backend.
* **Pass / Fail:** [ ]

---

### TC-D2-08: FR-06 Inactivity Review & Safe Provenance
* **Objective:** Verify stale or unavailable activity data is marked strictly as `Unknown` without false assumptions.
* **Steps:**
  1. Look at the **Last Active** column in the **Target List** table.
  2. Inspect contacts like `alex.dev`, `testuser`, etc.
* **Expected Result:**
  * Contacts with no direct verified activity show:  
    `Unknown (Safe default)` or `Unknown (Synthetic / Local Curated)`.
  * The system never labels a contact "Inactive" without a verified source and timestamp (complies with FR-06 & HR-02).
* **Pass / Fail:** [ ]

---

### TC-D2-09: FR-13 Snapscore Feature Gate & Policy Disclosures
* **Objective:** Verify policy disclaimers protect user against unauthorized claims.
* **Steps:**
  1. Scroll down to the **Snapscore Gate** panel at the bottom of the dashboard.
  2. Review the disclaimers in the Setup Disclosure banner and Streak panel.
* **Expected Result:**
  * Displays a clear notice: App does NOT artificially boost or manipulate Snapscore.
  * Discloses that streak snaps are user-confirmed and not automated mass spam.
* **Pass / Fail:** [ ]

---

### TC-D2-10: Automated Test Suite Regression Check
* **Objective:** Verify 100% pass rate across all backend automated unit and integration tests.
* **Steps:**
  1. Open terminal in the project directory: `c:\Users\user\Desktop\Sanpchat-Appilot`.
  2. Run the command:
     ```bash
     py -m pytest backend/tests/ -v
     ```
* **Expected Result:**
  * All 15 tests pass with 0 failures:
    - `test_state_machine_transitions` PASSED
    - `test_state_machine_invalid_transition` PASSED
    - `test_state_machine_emergency_stop` PASSED
    - `test_contact_service_normalization_and_duplicates` PASSED
    - `test_audit_logger_redaction` PASSED
    - `test_api_status_and_contacts` PASSED
    - `test_adb_service_capabilities` PASSED
    - `test_find_bounds_xml_parsing` PASSED
    - `test_live_automation_flow_execution` PASSED
    - `test_live_automation_emergency_stop` PASSED
    - `test_live_api_endpoint` PASSED
    - `test_reminder_and_draft_checklist_crud` PASSED
    - `test_full_e2e_demo_flow` PASSED
    - `test_edge_case_duplicate_injection` PASSED
    - `test_audit_logs_retrieval_and_clear` PASSED
* **Pass / Fail:** [ ]

---

## Summary Sign-off Sheet
* **Tested By:** _________________________
* **Date:** 2026-10-27
* **Device / OS:** Infinix X6817 (Android 12, API 31)
* **Overall Outcome:** [ ] ALL PASS  |  [ ] PASS WITH NOTES  |  [ ] FAIL
