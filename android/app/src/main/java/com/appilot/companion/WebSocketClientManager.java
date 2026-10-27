package com.appilot.companion;

import android.os.Build;
import android.util.Log;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;
import org.json.JSONObject;

import java.net.URI;

public class WebSocketClientManager {
    private static final String TAG = "AppilotWS";
    private static WebSocketClientManager instance;

    private WebSocketClient webSocketClient;
    private boolean isConnected = false;
    private StatusListener statusListener;
    private final android.os.Handler reconnectHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private boolean isReconnecting = false;
    private String lastServerUrl;
    private String lastDeviceId;
    private boolean lastAccessibility;

    public interface StatusListener {
        void onConnectionChanged(boolean connected);
        void onCommandReceived(String command);
    }

    private WebSocketClientManager() {}

    public static synchronized WebSocketClientManager getInstance() {
        if (instance == null) {
            instance = new WebSocketClientManager();
        }
        return instance;
    }

    public void setStatusListener(StatusListener listener) {
        this.statusListener = listener;
    }

    public void connect(String serverUrl, String deviceId, boolean accessibilityEnabled) {
        this.lastServerUrl = serverUrl;
        this.lastDeviceId = deviceId;
        this.lastAccessibility = accessibilityEnabled;

        if (webSocketClient != null && isConnected && webSocketClient.isOpen()) {
            if (statusListener != null) {
                statusListener.onConnectionChanged(true);
            }
            return;
        }

        try {
            if (webSocketClient != null) {
                try { webSocketClient.close(); } catch (Exception ignored) {}
            }

            URI uri = new URI(serverUrl + "?device_id=" + deviceId);
            webSocketClient = new WebSocketClient(uri) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    isConnected = true;
                    isReconnecting = false;
                    Log.i(TAG, "Connected to backend WebSocket: " + uri);
                    sendHello(deviceId, accessibilityEnabled);
                    if (statusListener != null) {
                        statusListener.onConnectionChanged(true);
                    }
                }

                @Override
                public void onMessage(String message) {
                    Log.i(TAG, "Received message: " + message);
                    try {
                        JSONObject json = new JSONObject(message);
                        if (json.has("command")) {
                            String cmd = json.getString("command");
                            if (statusListener != null) {
                                statusListener.onCommandReceived(cmd);
                            }
                        }
                        // Handle Automation Action commands from backend
                        if ("EXECUTE_ACTION".equals(json.optString("type")) || json.has("action")) {
                            String action = json.optString("action");
                            JSONObject params = json.optJSONObject("params");
                            if (params == null) params = new JSONObject();
                            if (SnapchatAccessibilityService.getInstance() != null) {
                                SnapchatAccessibilityService.getInstance().handleCommand(action, params);
                            } else {
                                Log.w(TAG, "SnapchatAccessibilityService is not running; cannot execute action " + action);
                            }
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "JSON parse error", e);
                    }
                }

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    isConnected = false;
                    Log.w(TAG, "WebSocket closed: " + reason);
                    if (statusListener != null) {
                        statusListener.onConnectionChanged(false);
                    }
                    scheduleReconnect();
                }

                @Override
                public void onError(Exception ex) {
                    isConnected = false;
                    Log.e(TAG, "WebSocket error: " + (ex != null ? ex.getMessage() : "unknown"));
                    if (statusListener != null) {
                        statusListener.onConnectionChanged(false);
                    }
                    scheduleReconnect();
                }
            };
            webSocketClient.connect();
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize WebSocket client", e);
            scheduleReconnect();
        }
    }

    private void scheduleReconnect() {
        if (isReconnecting) return;
        isReconnecting = true;
        reconnectHandler.postDelayed(() -> {
            isReconnecting = false;
            if (!isConnected && lastServerUrl != null) {
                Log.i(TAG, "Auto-reconnecting to backend WebSocket...");
                connect(lastServerUrl, lastDeviceId, lastAccessibility);
            }
        }, 3000);
    }

    public void sendHello(String deviceId, boolean accessibilityEnabled) {
        try {
            JSONObject payload = new JSONObject();
            payload.put("device_id", deviceId);
            payload.put("model", Build.MANUFACTURER + " " + Build.MODEL);
            payload.put("android_version", "Android " + Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + ")");
            payload.put("accessibility_enabled", accessibilityEnabled);

            JSONObject msg = new JSONObject();
            msg.put("type", "DEVICE_HELLO");
            msg.put("payload", payload);

            sendMessage(msg.toString());
        } catch (Exception e) {
            Log.e(TAG, "Error formatting hello message", e);
        }
    }

    public void sendActionResult(String status, String reasonCode, String message) {
        try {
            JSONObject msg = new JSONObject();
            msg.put("type", "ACTION_RESULT");
            msg.put("status", status);
            msg.put("reason_code", reasonCode);
            msg.put("message", message);
            sendMessage(msg.toString());
        } catch (Exception e) {
            Log.e(TAG, "Error sending action result", e);
        }
    }

    public void sendMessage(String message) {
        if (webSocketClient != null && isConnected && webSocketClient.isOpen()) {
            try {
                webSocketClient.send(message);
            } catch (Exception e) {
                Log.e(TAG, "Error sending message", e);
            }
        }
    }

    public void disconnect() {
        if (webSocketClient != null) {
            try { webSocketClient.close(); } catch (Exception ignored) {}
        }
        isConnected = false;
        isReconnecting = false;
        reconnectHandler.removeCallbacksAndMessages(null);
    }

    public boolean isConnected() {
        return isConnected;
    }
}
