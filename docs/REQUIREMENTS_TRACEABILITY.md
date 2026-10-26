# Day 1: Requirements Traceability & Feature Classification Matrix
**Project:** Appilot Snapchat Companion  
**Document Version:** 1.0  
**Date:** Day 1 Delivery Baseline  

---

## 1. Feature Classification (P0 / P1 / Out-of-Scope)

| Requirement ID | Name | Category | Status / Gate | Acceptance Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **FR-01** | Setup & Disclosure | P0 (Must Deliver) | Implemented in Day 1 | Shows app scope, limitations, manual vs automated disclosure before workflow. |
| **FR-02** | Permission State Tracking | P0 (Must Deliver) | Implemented in Day 1 | Live detection of Accessibility, Overlay, and Notification permissions without nagging. |
| **FR-03** | Start / Pause / Stop Controls | P0 (Must Deliver) | Implemented in Day 1 | Deterministic state machine (`Idle` → `Ready` → `Reviewing` → `Running` → `Completed`/`Stopped`/`Failed`). Emergency Stop prevents any new action immediately. |
| **FR-04** | User-Curated Target List | P0 (Must Deliver) | Implemented in Day 1 | Local CRUD, whitespace trimming, lowercase normalization, duplicate detection. |
| **FR-05** | Review Before Consequential Action | P0 (Must Deliver) | Foundation in Day 1 | Explicit confirmation dialog with target count and names before committing any action. |
| **FR-06** | Inactivity Review (Threshold) | P1 (Stretch) | Day 2 Planned | Synthetic data only. Any missing/stale data is explicitly tagged `Unknown`, never inferred inactive. |
| **FR-07** | Streak Reminders | P0 (Must Deliver) | Foundation in Day 1 | Local reminder creation with recipient label & local time. User executes in Snapchat. |
| **FR-08** | Snap Draft / Checklist | P0 (Must Deliver) | Foundation in Day 1 | Local draft notes and checklist; no autonomous sending to Snapchat recipients. |
| **FR-09** | Honest Result Status Model | P0 (Must Deliver) | Implemented in Day 1 | States: `Completed`, `Cancelled`, `Failed`, `Skipped`, `Needs user action`, `Unknown`. Never report fake success. |
| **FR-10** | Audit Log & Telemetry | P0 (Must Deliver) | Implemented in Day 1 | Real-time event log with timestamp, workflow, result, non-sensitive reason code. Zero passwords/tokens stored. |
| **FR-11** | Settings & Persistence | P0 (Must Deliver) | Implemented in Day 1 | Settings, curated contacts, and audit logs persist across app/server restarts. |
| **FR-12** | Deterministic Demo Mode | P0 (Must Deliver) | Implemented in Day 1 | Synthetic test suite to demonstrate success, failure, cancellation, duplicates without changing real accounts. |
| **FR-13** | Snapscore Feature Gate | P0 (Must Deliver) | Implemented in Day 1 | Permanent disclaimer and hard gate: App does NOT artificially boost or manipulate Snapscore. |
| **OUT-01** | Autonomous Bulk Adding / Removing | Out of Scope | BLOCKED | Snapchat ToS / Google Play prohibition. Requires official API / written authorization. |
| **OUT-02** | Anti-detection / CAPTCHA bypass | Out of Scope | BLOCKED | Security violation. Strictly excluded. |
| **OUT-03** | Credential Harvesting / Scraping | Out of Scope | BLOCKED | Storing Snapchat passwords or scraping private tokens is strictly prohibited. |

---

## 2. Non-Functional Requirements (NFR) Coverage

* **NFR-01 (Reliability):** Zero silent crashes. Any error transitions state machine to `Failed` or `Needs User Action` with user-readable message.
* **NFR-02 (Responsiveness):** Local UI and WebSocket dispatch latency under 100ms.
* **NFR-03 (Privacy):** Only local curated data is handled; zero external transmission of sensitive personal credentials.
* **NFR-04 (Security):** No hardcoded secrets, session tokens, or private messages in storage or logs.
* **NFR-05 (Transparency):** Clear indicators distinguishing Simulated, Draft, Pending, and Verified results.
* **NFR-08 (Maintainability):** Clean modular separation between Frontend (React), Backend Orchestrator (Python), and Android Client (Java).
