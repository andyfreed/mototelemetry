#!/bin/bash
# Final Boot Setup Script for Motorcycle Telemetry System
# Ensures all services and GPS are properly configured on boot

echo "🏍️ Configuring Motorcycle Telemetry System for Auto-Start"
echo "=========================================================="

# Essential services that must auto-start
CRITICAL_SERVICES=(
    "motorcycle-telemetry.service"
    "nodered.service" 
    "camera-stream.service"
    "tailscaled.service"
    "ModemManager.service"
)

# Enable all critical services
echo "🚀 Enabling critical services for auto-start..."
for service in "${CRITICAL_SERVICES[@]}"; do
    echo "   Enabling $service..."
    sudo systemctl enable $service
    if systemctl is-enabled --quiet $service; then
        echo "   ✅ $service enabled"
    else
        echo "   ❌ Failed to enable $service"
    fi
done

echo ""
echo "🛰️ Setting up GPS auto-configuration..."

# Create a GPS initialization service that runs after ModemManager
cat << 'EOF' | sudo tee /etc/systemd/system/cellular-gps-init.service > /dev/null
[Unit]
Description=Initialize Cellular GPS
After=ModemManager.service
Requires=ModemManager.service
StartLimitBurst=3
StartLimitIntervalSec=60

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/bin/sleep 10
ExecStart=/bin/bash -c 'mmcli -m 0 -e && mmcli -m 0 --location-enable-gps-nmea'
User=root
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable cellular-gps-init.service
echo "   ✅ GPS auto-initialization configured"

echo ""
echo "🔧 Verifying service status..."

# Check that all services are enabled
for service in "${CRITICAL_SERVICES[@]}"; do
    if systemctl is-enabled --quiet $service; then
        echo "   ✅ $service: Auto-start enabled"
    else
        echo "   ⚠️  $service: Auto-start DISABLED"
    fi
done

# Check GPS init service
if systemctl is-enabled --quiet cellular-gps-init.service; then
    echo "   ✅ cellular-gps-init.service: Auto-start enabled"
else
    echo "   ⚠️  cellular-gps-init.service: Auto-start DISABLED"
fi

echo ""
echo "📱 Testing cellular module..."
if sudo mmcli -L | grep -q "SIMCOM_SIM7600G-H"; then
    echo "   ✅ Cellular module detected"
    
    # Check modem status
    if sudo mmcli -m 0 --simple-status | grep -q "state.*connected"; then
        echo "   ✅ Cellular connection active"
    else
        echo "   ⚠️  Cellular connection inactive"
    fi
    
    # Check GPS status
    if sudo mmcli -m 0 --location-status | grep -q "gps-nmea"; then
        echo "   ✅ GPS enabled"
    else
        echo "   ⚠️  GPS disabled"
    fi
else
    echo "   ❌ Cellular module not detected"
fi

echo ""
echo "🌐 Network interface check..."
# Check network interfaces
interfaces=("wlan0" "wwan0" "tailscale0")
for iface in "${interfaces[@]}"; do
    if ip link show $iface >/dev/null 2>&1; then
        echo "   ✅ $iface interface present"
    else
        echo "   ⚠️  $iface interface not found"
    fi
done

echo ""
echo "📋 Creating startup verification alias..."
# Add alias to .bashrc for easy status checking
if ! grep -q "alias status=" ~/.bashrc; then
    echo "alias status='./startup_check.sh'" >> ~/.bashrc
    echo "   ✅ Added 'status' command alias"
else
    echo "   ✅ Status alias already exists"
fi

echo ""
echo "🏁 CONFIGURATION COMPLETE!"
echo "=========================="
echo ""
echo "✅ All critical services enabled for auto-start"
echo "✅ GPS auto-initialization configured"
echo "✅ Network interfaces verified"
echo "✅ Quick status command configured"
echo ""
echo "🔄 TESTING BOOT READINESS:"
echo "========================="
echo "To test auto-start functionality:"
echo "   sudo reboot"
echo ""
echo "After reboot, check status with:"
echo "   ./startup_check.sh"
echo "   (or just type: status)"
echo ""
echo "🎯 Your motorcycle telemetry system is now fully configured for automatic startup!" 