package com.appilot.companion;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Rect;
import android.os.Bundle;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class SnapchatAccessibilityService extends AccessibilityService {
    private static final String TAG = "AppilotService";
    private static SnapchatAccessibilityService instance;
    private boolean isAssisting = false;

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        Log.i(TAG, "SnapchatAccessibilityService connected and ready.");
        WebSocketClientManager.getInstance().sendActionResult("COMPLETED", "ACCESSIBILITY_ENABLED", "Accessibility service active and bound.");
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
                Log.d(TAG, "Snapchat window changed: " + event.getClassName());
                WebSocketClientManager.getInstance().sendActionResult(
                    "COMPLETED",
                    "SNAPCHAT_WINDOW",
                    "Snapchat window: " + event.getClassName()
                );
            }
        }
    }

    /**
     * Executes automation action dispatched from backend WebSocket
     */
    public boolean handleCommand(String action, JSONObject params) {
        Log.i(TAG, "Executing command: " + action + " with params: " + params);
        try {
            switch (action) {
                case "SEARCH_USER": {
                    String username = params.optString("username", "");
                    return performSearchUser(username);
                }
                case "CLICK_ADD": {
                    String username = params.optString("username", "");
                    return performClickAdd(username);
                }
                case "CLICK_NODE_BY_TEXT": {
                    String text = params.optString("text", "");
                    return clickFirstNodeWithText(text);
                }
                case "CLICK_COORDINATES": {
                    float x = (float) params.optDouble("x", 0);
                    float y = (float) params.optDouble("y", 0);
                    return tapCoordinates(x, y);
                }
                case "GO_BACK": {
                    return performGlobalAction(GLOBAL_ACTION_BACK);
                }
                case "DUMP_HIERARCHY": {
                    sendHierarchyDump();
                    return true;
                }
                default:
                    Log.w(TAG, "Unknown action: " + action);
                    return false;
            }
        } catch (Exception e) {
            Log.e(TAG, "Error executing action " + action, e);
            WebSocketClientManager.getInstance().sendActionResult("FAILED", "ACTION_ERROR", "Action " + action + " failed: " + e.getMessage());
            return false;
        }
    }

    public boolean performSearchUser(String username) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            WebSocketClientManager.getInstance().sendActionResult("FAILED", "ROOT_NULL", "Cannot access active window content");
            return false;
        }

        // Try finding search input or search icon
        AccessibilityNodeInfo searchNode = findNodeByViewIdSubstring(root, "search-textfield");
        if (searchNode == null) {
            searchNode = findNodeByViewIdSubstring(root, "hova_header_search_icon");
        }
        if (searchNode == null) {
            searchNode = findNodeFuzzy(root, "Search");
        }
        if (searchNode == null) {
            searchNode = findNodeByViewIdSubstring(root, "search");
        }

        if (searchNode != null) {
            searchNode.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            searchNode.performAction(AccessibilityNodeInfo.ACTION_FOCUS);

            Bundle args = new Bundle();
            args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, username);
            boolean textSet = searchNode.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);

            WebSocketClientManager.getInstance().sendActionResult(
                textSet ? "COMPLETED" : "NEEDS_USER_ACTION",
                "SEARCH_ENTERED",
                "Target @" + username + " entered into Snapchat search bar."
            );
            return textSet;
        } else {
            WebSocketClientManager.getInstance().sendActionResult("UNKNOWN", "SEARCH_BAR_NOT_FOUND", "Search bar not directly matched in active window.");
            return false;
        }
    }

    public boolean performClickAdd(String targetUsername) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;

        // Priority 1: Match by Snapchat exact resource-id
        AccessibilityNodeInfo addNode = findNodeByViewIdSubstring(root, "add-friend-button");
        if (addNode == null) {
            addNode = findNodeByViewIdSubstring(root, "subscribe-button");
        }
        // Priority 2: Fuzzy search text and content-desc
        if (addNode == null) {
            addNode = findNodeFuzzy(root, "Add");
        }
        if (addNode == null) {
            addNode = findNodeFuzzy(root, "Subscribe");
        }

        if (addNode != null) {
            boolean clicked = false;
            if (addNode.isClickable()) {
                clicked = addNode.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            }
            if (!clicked && addNode.getParent() != null && addNode.getParent().isClickable()) {
                clicked = addNode.getParent().performAction(AccessibilityNodeInfo.ACTION_CLICK);
            }
            if (!clicked) {
                // If not clickable via action, dispatch gesture tap on node bounds
                Rect rect = new Rect();
                addNode.getBoundsInScreen(rect);
                if (rect.width() > 0 && rect.height() > 0) {
                    clicked = tapCoordinates(rect.centerX(), rect.centerY());
                }
            }

            WebSocketClientManager.getInstance().sendActionResult(
                clicked ? "COMPLETED" : "FAILED",
                "ADD_BUTTON_CLICKED",
                "Tapped 'Add' button for @" + targetUsername + " in Snapchat."
            );
            return clicked;
        } else {
            WebSocketClientManager.getInstance().sendActionResult("UNKNOWN", "ADD_BUTTON_NOT_FOUND", "Add button for @" + targetUsername + " not found on screen.");
            return false;
        }
    }

    public boolean clickFirstNodeWithText(String text) {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return false;

        List<AccessibilityNodeInfo> nodes = root.findAccessibilityNodeInfosByText(text);
        if (nodes != null && !nodes.isEmpty()) {
            for (AccessibilityNodeInfo node : nodes) {
                if (node.isClickable()) {
                    return node.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                } else if (node.getParent() != null && node.getParent().isClickable()) {
                    return node.getParent().performAction(AccessibilityNodeInfo.ACTION_CLICK);
                }
            }
        }
        return false;
    }

    public boolean tapCoordinates(float x, float y) {
        Path swipePath = new Path();
        swipePath.moveTo(x, y);
        GestureDescription.Builder gestureBuilder = new GestureDescription.Builder();
        gestureBuilder.addStroke(new GestureDescription.StrokeDescription(swipePath, 0, 50));
        return dispatchGesture(gestureBuilder.build(), null, null);
    }

    private AccessibilityNodeInfo findNodeFuzzy(AccessibilityNodeInfo root, String query) {
        if (root == null) return null;
        List<AccessibilityNodeInfo> byText = root.findAccessibilityNodeInfosByText(query);
        if (byText != null && !byText.isEmpty()) {
            return byText.get(0);
        }
        return searchRecursiveByContentDesc(root, query.toLowerCase());
    }

    private AccessibilityNodeInfo searchRecursiveByContentDesc(AccessibilityNodeInfo node, String queryLower) {
        if (node == null) return null;
        CharSequence desc = node.getContentDescription();
        if (desc != null && desc.toString().toLowerCase().contains(queryLower)) {
            return node;
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo found = searchRecursiveByContentDesc(child, queryLower);
            if (found != null) return found;
        }
        return null;
    }

    private AccessibilityNodeInfo findNodeByViewIdSubstring(AccessibilityNodeInfo node, String queryLower) {
        if (node == null) return null;
        String viewId = node.getViewIdResourceName();
        if (viewId != null && viewId.toLowerCase().contains(queryLower)) {
            return node;
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            AccessibilityNodeInfo found = findNodeByViewIdSubstring(child, queryLower);
            if (found != null) return found;
        }
        return null;
    }

    public void sendHierarchyDump() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return;

        try {
            JSONArray array = new JSONArray();
            dumpNodeRecursive(root, array);
            JSONObject payload = new JSONObject();
            payload.put("type", "HIERARCHY_DUMP");
            payload.put("nodes", array);
            WebSocketClientManager.getInstance().sendMessage(payload.toString());
        } catch (Exception e) {
            Log.e(TAG, "Error generating hierarchy dump", e);
        }
    }

    private void dumpNodeRecursive(AccessibilityNodeInfo node, JSONArray array) {
        if (node == null) return;
        try {
            JSONObject obj = new JSONObject();
            if (node.getText() != null) obj.put("text", node.getText().toString());
            if (node.getContentDescription() != null) obj.put("desc", node.getContentDescription().toString());
            if (node.getViewIdResourceName() != null) obj.put("id", node.getViewIdResourceName());
            obj.put("class", node.getClassName() != null ? node.getClassName().toString() : "");
            obj.put("clickable", node.isClickable());

            Rect bounds = new Rect();
            node.getBoundsInScreen(bounds);
            obj.put("bounds", bounds.left + "," + bounds.top + "," + bounds.right + "," + bounds.bottom);
            array.put(obj);
        } catch (Exception e) {
            // Ignore format errors
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            dumpNodeRecursive(node.getChild(i), array);
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

