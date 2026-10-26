# Day 1: Platform Compliance & Feasibility Note
**Project:** Appilot Snapchat Companion  
**Baseline Date:** Day 1 Delivery Baseline  

---

## 1. Regulatory & Platform Guidance

### A. Snapchat Terms of Service (§ Restrictions on Use)
* **Prohibition:** Snap Inc. explicitly prohibits unauthorized third-party automation, scripts, bots, scrapers, or session-hijacking tools.
* **Account Safety Risk:** Any non-human high-frequency action or unofficial API reverse engineering triggers account locks, device bans, or permanent account deletion.
* **Mitigation / Architecture Decision:**
  * No unauthorized live automation is executed directly against the Snapchat backend.
  * The system functions strictly as an **Assisted Companion** with user-confirmed review gates.
  * Actions in Day 1–4 are demonstrated via **Deterministic Demo Simulation** and **Manual User Reminders/Drafts**.

### B. Google Play Developer Policy (§ Accessibility API)
* **Prohibition:** Google Play strictly restricts `AccessibilityService` to assistive tools for persons with disabilities or explicitly narrow, user-approved utilities. Using AccessibilityService to automate clicks or circumvent another application's security controls without clear user consent is grounds for immediate app removal.
* **Mitigation / Architecture Decision:**
  * AccessibilityService is implemented with explicit user opt-in, clear purpose disclosure on launch, and continuous visibility.
  * The service is used solely for passive window state detection (detecting if Snapchat is foregrounded) and guided user assistance, NOT autonomous headless botting.
  * An immediate **Emergency STOP** button can disconnect and stop the service at any moment.

---

## 2. Explicit Feature Gates

```
+-------------------------------------------------------------+
|                     FEATURE GATE MATRIX                     |
+------------------------------------+------------------------+
| Feature                            | Gate Status            |
+------------------------------------+------------------------+
| Synthetic Demo Mode                | ENABLED (Default)      |
| Curated Target List Management     | ENABLED (Local DB)     |
| Streak & Snap Local Reminders      | ENABLED (Local Device) |
| Transparent Audit Telemetry        | ENABLED (Local JSON)   |
| Live Unattended Mass Action        | BLOCKED (Requires ToS) |
| Reverse-Engineered Private APIs    | BLOCKED (Security Risk)|
| Artificial Snapscore Inflation     | BLOCKED (Prohibited)   |
+------------------------------------+------------------------+
```
