#!/bin/bash
# Setup script to ensure all services persist after reboot

echo "🔧 Setting up boot persistence for motorcycle telemetry system..."

# 1. Create gpsd service override
echo "📡 Configuring gpsd service..."
sudo mkdir -p /etc/systemd/system/gpsd.service.d/
sudo tee /etc/systemd/system/gpsd.service.d/override.conf > /dev/null << 'EOF'
[Service]
ExecStart=
ExecStart=/usr/sbin/gpsd -N -n /dev/ttyACM1
EOF

# 2. Ensure gpsd starts after USB devices are ready
sudo tee /etc/systemd/system/gpsd-wait.service > /dev/null << 'EOF'
[Unit]
Description=Wait for GPS device before starting gpsd
Before=gpsd.service
After=dev-ttyACM1.device
Wants=dev-ttyACM1.device

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'for i in {1..30}; do [ -e /dev/ttyACM1 ] && break || sleep 1; done'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# 3. Enable all services
echo "✅ Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable gpsd-wait.service
sudo systemctl enable gpsd.service
sudo systemctl enable motorcycle-telemetry.service
sudo systemctl enable nodered.service

# 4. Create startup check script
echo "📝 Creating startup verification script..."
sudo tee /usr/local/bin/check-motorcycle-services.sh > /dev/null << 'EOF'
#!/bin/bash
# Check motorcycle telemetry services status

echo "🏍️ Motorcycle Telemetry System Status Check"
echo "=========================================="

# Check GPS device
if [ -e /dev/ttyACM1 ]; then
    echo "✅ GPS Device: /dev/ttyACM1 found"
else
    echo "❌ GPS Device: /dev/ttyACM1 NOT FOUND"
fi

# Check services
for service in gpsd motorcycle-telemetry nodered; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
        echo "   Starting $service..."
        sudo systemctl start $service
    fi
done

# Check GPS data
echo ""
echo "📡 GPS Status:"
timeout 5 gpspipe -w -n 5 | grep -E "(lat|lon)" | head -1 || echo "No GPS data yet"

echo ""
echo "🌐 Dashboard URL: http://$(hostname -I | awk '{print $1}'):1880/ui"
EOF

sudo chmod +x /usr/local/bin/check-motorcycle-services.sh

# 5. Add to crontab for boot check
echo "⏰ Adding boot check to crontab..."
(crontab -l 2>/dev/null | grep -v "check-motorcycle-services"; echo "@reboot sleep 30 && /usr/local/bin/check-motorcycle-services.sh > /home/pi/motorcycle_data/boot_check.log 2>&1") | crontab -

# 6. Create systemd service for telemetry virtual environment activation
echo "🐍 Ensuring Python virtual environment persists..."
sudo tee /etc/systemd/system/motorcycle-telemetry.service > /dev/null << 'EOF'
[Unit]
Description=Motorcycle Telemetry System
After=network.target gpsd.service
Wants=gpsd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment="PATH=/home/pi/telemetry-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/pi/telemetry-env/bin/python /home/pi/motorcycle_telemetry.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Reload systemd
sudo systemctl daemon-reload

echo ""
echo "✅ Boot persistence setup complete!"
echo ""
echo "📋 Summary of what will happen on reboot:"
echo "   1. GPS device will be waited for (up to 30 seconds)"
echo "   2. gpsd will start with /dev/ttyACM1"
echo "   3. Motorcycle telemetry will start with enhanced GPS"
echo "   4. Node-RED dashboard will be available"
echo "   5. Boot check will run and log to ~/motorcycle_data/boot_check.log"
echo ""
echo "🔄 To test: sudo reboot"
echo "📊 After reboot, check status with: /usr/local/bin/check-motorcycle-services.sh" 