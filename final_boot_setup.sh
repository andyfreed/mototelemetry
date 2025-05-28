#!/bin/bash
# Final boot persistence setup for motorcycle telemetry

echo "🔧 Final boot persistence setup..."

# 1. Fix gpsd to start without socket dependency
sudo tee /etc/systemd/system/gpsd.service > /dev/null << 'EOF'
[Unit]
Description=GPS (Global Positioning System) Daemon
After=network.target

[Service]
Type=forking
ExecStart=/usr/sbin/gpsd -P /var/run/gpsd.pid -N -n /dev/ttyACM1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 2. Create a startup script that runs after boot
sudo tee /etc/rc.local > /dev/null << 'EOF'
#!/bin/bash
# Motorcycle telemetry startup script

# Wait for system to settle
sleep 20

# Log startup
echo "$(date) - Starting motorcycle telemetry services" >> /home/pi/motorcycle_data/boot.log

# Kill any existing gpsd processes
killall gpsd 2>/dev/null

# Start gpsd manually with the GPS device
/usr/sbin/gpsd -N -n /dev/ttyACM1 &

# Give gpsd time to start
sleep 5

# Ensure Node-RED is running
systemctl is-active --quiet nodered || systemctl start nodered

# Ensure telemetry is running
systemctl is-active --quiet motorcycle-telemetry || systemctl start motorcycle-telemetry

echo "$(date) - All services started" >> /home/pi/motorcycle_data/boot.log

exit 0
EOF

sudo chmod +x /etc/rc.local

# 3. Enable rc-local service
sudo systemctl enable rc-local

# 4. Create a simple monitoring script
sudo tee /home/pi/check_services.sh > /dev/null << 'EOF'
#!/bin/bash
echo "🏍️ Motorcycle Telemetry Status"
echo "=============================="
echo ""
echo "📡 GPS Process:"
pgrep -a gpsd || echo "Not running"
echo ""
echo "🌐 Services:"
for service in motorcycle-telemetry nodered; do
    if systemctl is-active --quiet $service; then
        echo "✅ $service: Running"
    else
        echo "❌ $service: Not running"
    fi
done
echo ""
echo "📍 GPS Data:"
timeout 3 gpspipe -w -n 1 2>/dev/null | grep -o '"lat":[^,]*' | head -1 || echo "No GPS data"
echo ""
echo "🌐 Dashboard: http://$(hostname -I | awk '{print $1}'):1880/ui"
EOF

chmod +x /home/pi/check_services.sh

# 5. Reload systemd
sudo systemctl daemon-reload

echo ""
echo "✅ Final boot persistence setup complete!"
echo ""
echo "📋 What will happen on reboot:"
echo "   1. System will wait 20 seconds for USB devices"
echo "   2. gpsd will start with your GPS on /dev/ttyACM1"
echo "   3. Node-RED will start"
echo "   4. Motorcycle telemetry will start with enhanced GPS"
echo ""
echo "🔍 To check status after reboot: ./check_services.sh"
echo "📄 Boot log will be at: ~/motorcycle_data/boot.log" 