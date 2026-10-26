package com.appilot.companion;

import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.TextUtils;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity implements WebSocketClientManager.StatusListener {

    private TextView tvAccessibilityStatus;
    private TextView tvWsStatus;
    private Button btnOpenAccessibility;
    private Button btnEmergencyStop;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvAccessibilityStatus = findViewById(R.id.tv_accessibility_status);
        tvWsStatus = findViewById(R.id.tv_ws_status);
        btnOpenAccessibility = findViewById(R.id.btn_open_accessibility);
        btnEmergencyStop = findViewById(R.id.btn_emergency_stop);

        btnOpenAccessibility.setOnClickListener(v -> {
            Intent intent = new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS);
            startActivity(intent);
        });

        btnEmergencyStop.setOnClickListener(v -> {
            triggerEmergencyStop();
        });

        WebSocketClientManager.getInstance().setStatusListener(this);
        connectToBackend();
    }

    @Override
    protected void onResume() {
        super.onResume();
        updateServiceStatus();
    }

    private void updateServiceStatus() {
        boolean isServiceEnabled = isAccessibilityServiceEnabled(this, SnapchatAccessibilityService.class);
        if (isServiceEnabled) {
            tvAccessibilityStatus.setText(R.string.status_accessibility_on);
            tvAccessibilityStatus.setTextColor(Color.parseColor("#22C55E"));
            btnOpenAccessibility.setText("Accessibility Service Enabled");
            btnOpenAccessibility.setEnabled(false);
        } else {
            tvAccessibilityStatus.setText(R.string.status_accessibility_off);
            tvAccessibilityStatus.setTextColor(Color.parseColor("#F59E0B"));
            btnOpenAccessibility.setText(R.string.btn_enable_accessibility);
            btnOpenAccessibility.setEnabled(true);
        }
    }

    private void connectToBackend() {
        String deviceId = "device_" + Build.SERIAL != null ? Build.SERIAL : "android_test_device";
        // Connect via localhost (standard when adb reverse tcp:8000 tcp:8000 is run) or emulator 10.0.2.2
        String wsUrl = "ws://10.0.2.2:8000/ws/device";
        boolean accessibilityActive = isAccessibilityServiceEnabled(this, SnapchatAccessibilityService.class);
        WebSocketClientManager.getInstance().connect(wsUrl, deviceId, accessibilityActive);
    }

    private void triggerEmergencyStop() {
        Toast.makeText(this, "Emergency STOP Triggered!", Toast.LENGTH_SHORT).show();
        if (SnapchatAccessibilityService.getInstance() != null) {
            SnapchatAccessibilityService.getInstance().stopAssistedAction();
        }
        WebSocketClientManager.getInstance().sendActionResult("CANCELLED", "USER_EMERGENCY_STOP", "User pressed in-app Emergency STOP button");
    }

    @Override
    public void onConnectionChanged(boolean connected) {
        runOnUiThread(() -> {
            if (connected) {
                tvWsStatus.setText(R.string.status_ws_connected);
                tvWsStatus.setTextColor(Color.parseColor("#22C55E"));
            } else {
                tvWsStatus.setText(R.string.status_ws_disconnected);
                tvWsStatus.setTextColor(Color.parseColor("#EF4444"));
            }
        });
    }

    @Override
    public void onCommandReceived(String command) {
        if ("STOP".equalsIgnoreCase(command)) {
            runOnUiThread(this::triggerEmergencyStop);
        }
    }

    public static boolean isAccessibilityServiceEnabled(Context context, Class<?> service) {
        String expectedComponentName = context.getPackageName() + "/" + service.getName();
        String enabledServices = Settings.Secure.getString(
                context.getContentResolver(),
                Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        );
        if (enabledServices == null) return false;
        TextUtils.SimpleStringSplitter colonSplitter = new TextUtils.SimpleStringSplitter(':');
        colonSplitter.setString(enabledServices);
        while (colonSplitter.hasNext()) {
            String componentName = colonSplitter.next();
            if (componentName.equalsIgnoreCase(expectedComponentName)) {
                return true;
            }
        }
        return false;
    }
}
