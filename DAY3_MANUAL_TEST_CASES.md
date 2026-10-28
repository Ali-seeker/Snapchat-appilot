# 🚀 Day 3 Manual Test Cases Guide: Appilot Dashboard
**Project:** Appilot Snapchat Companion & Automation Suite  
**Dashboard URL:** [http://localhost:5173](http://localhost:5173)  
**Target Environment:** Infinix X6817 (Android 12) • Snapchat `v14.29.0.50`  

---

## 📋 Pre-Test Checklist (Testing se pehle yeh check karein)
- [ ] Mobile USB Cable se PC ke sath connected ho aur Screen On ho.
- [ ] Dashboard ke top bar par **`Snapchat v14.29.0.50`** aur **`Infinix X6817 (Connected)`** ka green pulsing badge nazar aa raha ho.
- [ ] Snapchat app mobile par open ho (Camera landing page par).

---

## 🧪 Test Case 1: Quick Actions — Add Friends (Bulk Follow)
*Goal: Dashboard ke 1-click Quick Action card se suggestions list se friends add karna.*

### Steps:
1. Dashboard ke **Home** tab par jayein.
2. **Quick Actions** section mein pehle yellow card: **"Add Friends"** par click karein.
3. Ek live popup open hoga: *"Live Workflow Execution • Bulk Follow Automation (Quick Add Suggestions)"*.
4. Mobile screen ko dekhein:
   - Bot Snapchat ke Add Friends page par jayega.
   - Quick Add section mein candidates ke samne **"+ Add"** button par tap karega.
   - Task complete hone ke baad bot camera landing screen par wapis aa jayega.
5. Modal mein **"Done / Close"** button click karein.

### Expected Result (Matlooba Nateeja):
- Dashboard modal par har step green checkmark ke sath show ho.
- Mobile par suggestions mein se 2–5 dost add hon aur screen cleanly camera landing par wapis aa jaye.
- **Activity** tab mein *"Added suggested friends"* ka log record ho jaye.

---

## 🧪 Test Case 2: Auto Snap Dispatch (Random Filter Lens & Send)
*Goal: Camera se snap lena, random lens swipe karna, friends select karna aur dispatch karna.*

### Steps:
1. Dashboard ke **Home** tab par **Quick Actions** mein blue card: **"Snap Reminders"** par click karein.  
   *(Ya sidebar se **Snap Reminders** tab par ja kar **"Send Snap Now"** click karein).*
2. Live Execution modal open hoga.
3. Mobile screen par monitor karein:
   - Bot hardware camera shutter button tap karega.
   - Screen par ek aesthetic lens filter swipe apply hoga.
   - Preview screen par bina kisi popup ya cancel dialog ke bottom-right blue **"Send To"** button tap hoga.
   - Friend list mein se contacts select honge (blue checkmarks show honge).
   - Bottom right paper plane icon par tap ho kar snap send ho jayegi.
   - Bot wapis camera landing par aa jayega.

### Expected Result:
- Snap chat feed mein contacts ko deliver ho jaye (Red delivered icon nazar aaye).
- Dashboard modal complete ho kar `COMPLETED` status show kare.

---

## 🧪 Test Case 3: Snapscore Booster (Multi-Cycle Score Multiplier)
*Goal: Multiple rounds mein continuous snaps send kar k legitimate Snapscore increase karna.*

### Steps:
1. Dashboard ke **Home** tab par **Quick Actions** mein green card: **"Streak Reminders"** par click karein.  
   *(Ya Enterprise Automation Hub mein **"Score Booster"** button click karein).*
2. Live modal open hoga: *"Snapscore Booster (3 Cycles)"*.
3. Mobile screen par dekhein:
   - **Cycle 1:** Snap capture hogi ➡️ friends select honge ➡️ send hogi.
   - **Anti-Ban Cooldown:** Bot 10 seconds ka safety pause lega taake Snapchat account flag na ho.
   - **Cycle 2:** Fresh snap capture hogi ➡️ select hogi ➡️ send hogi.
   - Final status `COMPLETED` ho jayega.

### Expected Result:
- Dono cycles smoothly complete hon.
- Snapchat profile khol kar check karein, Snapscore mein points increase ho chuke honge.

---

## 🧪 Test Case 4: Smart Bulk Unfollow (Engagement & No-Streak Filter)
*Goal: Jin doston ke sath streak nahi chal rahi unko smart filter kar ke remove karna.*

### Steps:
1. Dashboard ke **Home** tab par **Quick Actions** mein purple card: **"Remove Friends"** par click karein.
2. Live modal open hoga: *"Smart Unfollow (No Streak Filter)"*.
3. Mobile screen par monitor karein:
   - Bot Chat feed open karega.
   - Chat list scan kar ke aese dost dhoondega jinke sath 🔥 emoji (streak) nahi hai.
   - Friend ki row par long-press karega.
   - Context menu se **"Manage Friendship"** par tap karega.
   - Submenu khulte hi **"Remove Friend"** par tap karega.
   - Confirmation dialog mein **"Remove"** par tap karega.
   - Anti-ban rest (2-3 seconds) lega aur workflow finish karega.

### Expected Result:
- Woh dost jinki streak nahi thi Snapchat se remove ho jayenge.
- Dashboard par *"Successfully unfollowed friend [Reason: No active streak emoji (🔥) found]"* ka log aayega.

---

## 🧪 Test Case 5: Chained Routine (Morning Growth Workflow)
*Goal: Hero banner se 1-click full routine chalana (Auto Snap + Quick Add combined).*

### Steps:
1. Dashboard ke **Home** tab par Hero banner ke andar yellow button: **"Start Automation ➔"** par click karein.
2. Live modal open hoga: *"Chained Routine: Morning Growth"*.
3. Mobile screen par observe karein:
   - **Stage 1 (Auto Snap Dispatch):** Camera se snap capture hogi, lens swipe hoga, aur snap send ho jayegi.
   - **Cooldown:** Bot 6.3 seconds ka rest lega.
   - **Stage 2 (Quick Add Suggestions):** Bot Add Friends screen par ja kar naye friends add karega aur camera landing par wapis aa jayega.
4. Modal par `COMPLETED` show hoga.

### Expected Result:
- Dono stages bina kisi manual interference ke sequentially execute hon aur finish ho jayein.

---

## 🧪 Test Case 6: Safety Pause & Emergency Stop
*Goal: Real-time execution ke doran bot ko foran rokna (Emergency Stop).*

### Steps:
1. Koi bhi automation launch karein (e.g. Quick Add ya Snapscore Booster).
2. Live modal ke andar **"Pause"** button par click karein:
   - Bot wahi pause ho jayega aur status `PAUSED` ho jayega.
3. **"Resume"** par click karein ➡️ Bot agle step se continue karega.
4. Red **"Emergency Stop"** button par click karein.

### Expected Result:
- Bot foran phone par tamaam actions cancel kar dega aur status `STOPPED` ho jayega.
- Koi unwanted touch ya command run nahi hogi.

---

## 🧪 Test Case 7: Friend Management Table (Target Add / Delete / Filter)
*Goal: Naye target contacts add karna aur filter check karna.*

### Steps:
1. Left sidebar se **"Friends"** tab par click karein.
2. Search bar mein koi naam type karein (e.g. "Ayesha" ya "Alex").
3. Filter pills par click karein: `All`, `Active`, `Inactive`, `Unknown`.
4. Top right par **"+ Add Target Contact"** click karein:
   - Username: `@john.doe`
   - Display Name: `John Doe`
   - **"Add Friend Target"** click karein.
5. Table mein naya contact row appear ho jayegi. Checkbox select kar ke **"Bulk Add Selected"** ya **"Unfollow Selected"** test karein.

### Expected Result:
- Table instantly filter aur search kare. Naya contact database aur table mein instantly save ho jaye.

---

## 🧪 Test Case 8: Streak & Snap Reminders View
*Goal: Reminders schedule karna aur toggle switch on/off karna.*

### Steps:
1. Sidebar se **"Streak Reminders"** tab par click karein.
2. Kisi friend ke samne green toggle switch par click karein ➡️ Switch gray/paused ho jayega aur badge `Paused` ban jayega.
3. Wapis click karein ➡️ Switch green ho jayega aur badge `Active` ban jayega.
4. **"Add New Reminder"** button click kar ke naya schedule add karein.
5. Sidebar se **"Snap Reminders"** tab par ja kar lens filter setting (Random Aesthetic Lens / Natural) toggle karein.

### Expected Result:
- Toggles smooth animation ke sath react karein aur schedules save hon.

---

## 🧪 Test Case 9: Activity History & Audit Logs
*Goal: Tamam automation activities ka history record aur clear check karna.*

### Steps:
1. Sidebar se **"Activity"** tab par click karein.
2. Top filter pills test karein: `All`, `Completed`, `Failed`, `Pending`.
3. Check karein ke jo automations aap ne run ki hain unke exact step logs aur deltas (`+1`, `-1`, `📸`) nazar aa rahe hain.
4. Top right par **"Clear History"** click karein.

### Expected Result:
- Filters accurate results dikhayein aur Clear History par logs empty ho kar clean state show karein.
