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
        if (webSocketClient != null && isConnected) {
            return;
        }

        try {
            URI uri = new URI(serverUrl + "?device_id=" + deviceId);
            webSocketClient = new WebSocketClient(uri) {
                @Override
                public void onOpen(ServerHandshake handshakedata) {
                    isConnected = true;
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
                }

                @Override
                public void onError(Exception ex) {
                    isConnected = false;
                    Log.e(TAG, "WebSocket error: " + ex.getMessage());
                    if (statusListener != null) {
                        statusListener.onConnectionChanged(false);
                    }
                }
            };
            webSocketClient.connect();
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize WebSocket client", e);
        }
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
        if (webSocketClient != null && isConnected) {
            webSocketClient.send(message);
        }
    }

    public void disconnect() {
        if (webSocketClient != null) {
            webSocketClient.close();
        }
        isConnected = false;
    }

    public boolean isConnected() {
        return isConnected;
    }
}
