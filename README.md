# Appilot Snapchat Companion — Day 1 Delivery Baseline

**Project:** Appilot Snapchat Assisted Companion  
**Stack:** Python (Backend) • React (Frontend) • Java (Android APK)  
**Document Version:** 1.0 (Day 1 Complete Delivery)  

---

## 1. Executive Summary & Architecture

The Appilot Snapchat Companion is a user-directed, policy-compliant assisted companion designed for Snapchat social workflow review and maintenance without violating platform Terms of Service or Google Play Accessibility policies.

```
+-----------------------------------------------------------------------------------+
|                            REACT DASHBOARD (Frontend)                             |
|  - Real-time State Machine Display (Idle -> Ready -> Reviewing -> Running)        |
|  - FR-01 Setup & Transparency Disclosure                                          |
|  - FR-03/05 Consequential Action Confirmation & Emergency STOP                    |
|  - FR-04 User-Curated Target Contact Manager                                      |
|  - FR-12 Deterministic Demo Test Suite                                            |
|  - FR-09/10 Real-Time Audit Log & Telemetry Stream                                |
+----------------------------------------+------------------------------------------+
                                         | WebSocket / REST (:8000)
                                         v
+-----------------------------------------------------------------------------------+
|                            PYTHON FASTAPI (Backend)                               |
|  - State Machine Orchestrator (Idempotent transitions, emergency halt)            |
|  - ADB Manager (Device discovery, adb reverse port forwarding)                    |
|  - WebSocket Hub (/ws/client for Dashboard, /ws/device for Android APK)           |
|  - Contact Normalization & Duplicate Prevention Service                           |
|  - Privacy-compliant Audit Logger (Redacts tokens/credentials)                    |
|  - Synthetic Demo Engine (Success, duplicate, inactivity, failure recovery)       |
+----------------------------------------+------------------------------------------+
                                         | WebSocket (:8000 / reverse)
                                         v
+-----------------------------------------------------------------------------------+
|                             ANDROID APP (Java Native)                             |
|  - SnapchatAccessibilityService (Passive window state & safe assistance)          |
|  - WebSocketClientManager (Real-time device registration & stop sync)             |
|  - MainActivity (Setup disclosure, permission status, hardware STOP)              |
+-----------------------------------------------------------------------------------+
```

---

## 2. Day 1 Features Implemented & Verified

| Feature ID | Name | Status | Verification Evidence |
| :--- | :--- | :--- | :--- |
| **FR-01** | Setup & Transparency Disclosure | **COMPLETED** | Interactive panel in React and Android APK with mandatory user acknowledgement before workflow execution. |
| **FR-02** | Permission State Tracking | **COMPLETED** | Live detection of AccessibilityService, Notifications, and Backend WebSocket connection. |
| **FR-03** | Start, Pause, & Emergency STOP | **COMPLETED** | Deterministic state transitions; Emergency STOP halts backend, broadcasts to all connected devices, and logs cancellation. |
| **FR-04** | User-Curated Target List | **COMPLETED** | Full local CRUD, automatic lowercase normalization, whitespace trimming, and duplicate rejection. |
| **FR-05** | Pre-Execution Review Gate | **COMPLETED** | Confirmation modal displaying exact recipient count and usernames before starting. |
| **FR-09** | Honest Result Status Model | **COMPLETED** | Outcomes classified strictly as `COMPLETED`, `CANCELLED`, `FAILED`, `SKIPPED`, `NEEDS_USER_ACTION`, or `UNKNOWN`. |
| **FR-10** | Privacy-Safe Audit Logger | **COMPLETED** | Real-time event log with non-sensitive reason codes. Passwords, session tokens, and credentials automatically redacted. |
| **FR-11** | Local Persistence | **COMPLETED** | Curated contacts, preferences, and logs persisted safely to local storage. |
| **FR-12** | Deterministic Demo Engine | **COMPLETED** | Full synthetic test bench verifying Success, Duplicate Injection, Inactivity Policy, and Failure Recovery. |
| **FR-13** | Snapscore Feature Gate | **COMPLETED** | Permanent policy disclaimer and hard gate prohibiting artificial score manipulation. |
| **SC-01** | Clean Source Build | **COMPLETED** | Both Python, React, and Java Android projects compile cleanly from source. |
| **SC-02** | Debug APK Generation | **COMPLETED** | Built `app-debug.apk` (5.78 MB) located in `android/app/build/outputs/apk/debug/`. |

---

## 3. How to Run the System

### 1. Python Backend
```bash
# Option A: One-click launcher (from project root)
.\start_backend.bat

# Option B: Terminal command (from backend folder)
cd backend
.\.venv\Scripts\python run.py
```
* API runs at: `http://localhost:8000`
* Swagger docs: `http://localhost:8000/docs`
* WebSockets: `ws://localhost:8000/ws/client` and `ws://localhost:8000/ws/device`

### 2. React Frontend Dashboard
```bash
# Option A: One-click launcher (from project root)
.\start_frontend.bat

# Option B: Terminal command (from frontend folder)
cd frontend
npm run dev
```
* Dashboard runs at: `http://localhost:5173`

### 3. Android Companion APK
```bash
cd android

# Build Debug APK
.\gradlew.bat assembleDebug

# Install on connected device or emulator via ADB
adb install -r app\build\outputs\apk\debug\app-debug.apk

# Forward backend port so device can connect seamlessly
adb reverse tcp:8000 tcp:8000
```

---

## 4. Test Suite Execution

Run the complete backend unit, integration, and E2E test suite:
```bash
.\backend\.venv\Scripts\pytest -o asyncio_default_fixture_loop_scope=function backend\tests
```
**Test Results:** `9 passed, 0 failed (100% pass rate)`
