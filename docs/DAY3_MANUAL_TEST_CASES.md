# Day 3: End-to-End Manual Testing Guide & Acceptance Verification
**Project:** Snapchat Appilot (`Sanpchat-Appilot`)  
**Branch:** `day-3-resilience`  
**Target Hardware:** Infinix X6817 (`08265372BO000706`), Android 12  
**Target Application:** `com.snapchat.android`

---

## 1. Overview of Day 3 Delivered Capabilities

Day 3 transitions Snapchat Appilot into an end-to-end, production-grade automation suite with:
1. **Multi-Modal Bulk Follow:**
   - **Quick Add Suggestions:** Auto-adds recommended candidates with human touch pacing and scrolling.
   - **Search List:** Bulk adds specified usernames with realistic keystroke delays (80ms–180ms).
   - **Accept Incoming Requests:** Scans `Added Me` section and auto-accepts pending follower requests.
2. **Smart Bulk Unfollow with Engagement Filters:**
   - **No Streak (`🔥`):** Identifies and removes friends lacking an active streak emoji.
   - **Inactive / Dormant:** Filters friend chats dormant for > N days (e.g., >17 days, `2w`, `1mo`).
   - **Custom List:** Targets specific custom selected users.
   - **Execution Sequence:** Long-press row ➡️ `Manage Friendship` ➡️ `Remove Friend` ➡️ Confirm `Remove`.
3. **Auto Snap Dispatch:**
   - Triggers camera hardware shutter button.
   - Applies random aesthetic lens/color filters via horizontal swipe gestures across the viewfinder.
   - Opens Send To view, selects All Friends / candidate rows, and dispatches the Snap.
4. **Algorithmic Snapscore Acceleration Engine:**
   - **Research:** Text chats award 0 points. Snapscore only increases from photo/video Snaps sent and opened (+1 point per recipient).
   - **Implementation:** Automated multi-cycle photo capture, filter variation, and multi-recipient dispatch with anti-ban cooldowns (12s–25s).
5. **Chained & Scheduled Daily Routines:**
   - **Morning Growth:** Auto Snap + Quick Add Suggestions with inter-stage rest.
   - **Score & Clean:** Snapscore Booster + Unfollow Friends without Streak.
   - **All-in-One Power Suite:** Snap + Quick Add + Accept Incoming + Clean Inactive (>17d).
6. **Interruption Resilience & Anti-Ban Humanization:**
   - Automatic swipe-up dismissal of top system heads-up notifications.
   - In-app popup resilience without aborting the workflow.
   - Gaussian touch bounding offsets, variable keystrokes, and randomized rest pauses.
7. **Clean Dashboard UI:**
   - Intuitive visual cards, simple Urdu/English labels, one-click execution buttons.
   - High-signal audit logs filtering out raw internal accessibility noise.

---

## 2. Test Execution Matrix

### Test Case 1: Bulk Follow via Quick Add Suggestions
- **Action:**
  1. In the **Bulk Follow** card on the dashboard, ensure `Quick Add Suggestions` is selected.
  2. Select target count (e.g., 5 or 10 friends).
  3. Click **"Start Quick Add"**.
- **Expected Behavior:**
  - Phone opens Snapchat and navigates to the Add Friends page (`open_add_friends_page`).
  - Appilot scans `+ Add` buttons, taps with 1.8s–3.2s anti-ban jitter, and scrolls down for more candidates.
  - Dashboard Live Execution Modal streams: `Added X suggested friend(s). Total added: Y/10`.
  - Cleans up and returns to camera landing screen upon completion.

---

### Test Case 2: Accept Incoming Followers
- **Action:**
  1. In the **Bulk Follow** card, switch to `Accept Incoming`.
  2. Click **"Accept All Incoming Requests"**.
- **Expected Behavior:**
  - Navigates to Add Friends view.
  - Scans `Added Me` list for incoming requests.
  - Clicks `Accept` for pending follower items.
  - Returns to camera landing screen and logs `REQUESTS_ACCEPTED`.

---

### Test Case 3: Smart Bulk Unfollow (No Streak 🔥 Filter)
- **Action:**
  1. In the **Smart Bulk Unfollow** card, select `No Streak` (Missing 🔥 emoji).
  2. Set max removals (e.g., 3 or 5 friends).
  3. Click **"Unfollow Non-Streak Friends"**.
- **Expected Behavior:**
  - Appilot navigates to the Chat feed tab (`open_chat_screen`).
  - Scans visible friend rows for missing streak emoji (`🔥`).
  - For each non-streak friend:
    - Long-presses the chat item for 850ms.
    - Taps `Manage Friendship`.
    - Taps `Remove Friend`.
    - Taps `Remove` in confirmation modal.
  - Logs `[COMPLETED] Unfollowed 'Username' [Reason: No active streak emoji (🔥) found]`.
  - Returns cleanly to camera landing screen.

---

### Test Case 4: Smart Bulk Unfollow (Inactive >17 Days Filter)
- **Action:**
  1. In the **Smart Bulk Unfollow** card, select `Inactive`.
  2. Set inactivity threshold slider to `17 Days`.
  3. Click **"Unfollow Inactive >17d"**.
- **Expected Behavior:**
  - Navigates to Chat feed.
  - Inspects timestamps (`2w`, `3w`, `1mo`, `2mo`, etc.).
  - Executes friendship removal for dormant conversations exceeding 17 days.

---

### Test Case 5: Auto Snap Dispatch with Random Filter
- **Action:**
  1. In the **Auto Snap Dispatch** card, keep `Random Aesthetic Filter` and `Select All Friends` checked.
  2. Click **"Capture & Send Snap Now"**.
- **Expected Behavior:**
  - Phone verifies camera landing view.
  - Taps camera hardware shutter button (`capture_snap_photo`).
  - Performs 1 to 3 horizontal swipe gestures across the viewfinder to apply artistic lenses/filters.
  - Taps yellow `Send To` button.
  - Selects All Friends / candidate rows.
  - Taps `Send` button.
  - Returns cleanly to camera landing screen and logs `SNAP_SENT`.

---

### Test Case 6: Algorithmic Snapscore Booster
- **Action:**
  1. In the **Snapscore Algorithmic Booster** card, select `3 Cycles`.
  2. Click **"Launch Snapscore Booster (+45 pts)"**.
- **Expected Behavior:**
  - Executes 3 sequential cycles of Snap photo capture ➡️ random filter ➡️ multi-recipient dispatch.
  - Pauses for a realistic 12s–25s anti-ban cooldown between cycles.
  - Dashboard streams cycle progress and score estimations:
    `[Cycle 1/3] Snap delivered to 15 contacts. Estimated points gained: +15 (Total: +15)`.
    `[Cycle 2/3] Snap delivered to 15 contacts. Estimated points gained: +15 (Total: +30)`.
    `[Cycle 3/3] Snap delivered to 15 contacts. Estimated points gained: +15 (Total: +45)`.
  - State machine transitions cleanly to `COMPLETED`.

---

### Test Case 7: Chained Daily Routines
- **Action:**
  1. In the **Chained Daily Routines** card, click **"Run Morning Routine"**.
- **Expected Behavior:**
  - Stage 1: Dispatches Auto Snap to all contacts.
  - Resting pause: Inter-stage cooldown for 5 seconds.
  - Stage 2: Quick Adds 5 suggested friends.
  - Modal tracks overall progress across all stages.

---

### Test Case 8: Interruption Resilience & Emergency Stop
- **Action:**
  1. Trigger any active workflow (e.g. Snapscore Booster or Quick Add).
  2. While the routine is running, swipe a notification down from top or click **Emergency STOP** on dashboard.
- **Expected Behavior:**
  - If a system heads-up notification appears, Appilot immediately swipes up at the top edge (`dismiss_heads_up_notification`) and continues execution.
  - If user hits Emergency STOP, state machine immediately transitions to `STOPPED`, halts all hardware dispatches, and logs `USER_EMERGENCY_STOP`.

---

## 3. Automated Backend Unit Test Verification

To run the complete automated test suite verifying all Day 1, Day 2, and Day 3 functionality:

```powershell
py -m pytest backend/tests/ -v
```

**Expected Result:**
```text
backend/tests/test_backend.py . . . . . .
backend/tests/test_day2_live_automation.py . . . . . .
backend/tests/test_day3_features.py . . . . . . .
backend/tests/test_e2e_flow.py . . .
======================= 22 passed in 4.90s =======================
```
