package com.appilot.companion;

import android.accessibilityservice.AccessibilityService;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

public class SnapchatAccessibilityService extends AccessibilityService {
    private static final String TAG = "AppilotService";
    private static SnapchatAccessibilityService instance;
    private boolean isAssisting = false;

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.i(TAG, "SnapchatAccessibilityService connected.");
        WebSocketClientManager.getInstance().sendActionResult("COMPLETED", "ACCESSIBILITY_ENABLED", "Accessibility service active and connected.");
    }

    public static boolean isServiceRunning() {
        return instance != null;
    }

    public static SnapchatAccessibilityService getInstance() {
        return instance;
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;

        CharSequence packageName = event.getPackageName();
        if (packageName != null && packageName.toString().equals("com.snapchat.android")) {
            int eventType = event.getEventType();
            if (eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
                Log.d(TAG, "Snapchat foreground window state changed: " + event.getClassName());
                WebSocketClientManager.getInstance().sendActionResult("UNKNOWN", "SNAPCHAT_FOREGROUND", "Snapchat window detected: " + event.getClassName());
            }
        }
    }

    public void stopAssistedAction() {
        isAssisting = false;
        Log.i(TAG, "Assisted action stopped immediately via safety command.");
        WebSocketClientManager.getInstance().sendActionResult("CANCELLED", "USER_EMERGENCY_STOP", "Assisted service halted via stop command.");
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "Accessibility Service interrupted.");
        isAssisting = false;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
        Log.i(TAG, "Accessibility Service destroyed.");
    }
}
