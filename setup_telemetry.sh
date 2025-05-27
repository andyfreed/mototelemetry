#!/bin/bash
# Motorcycle Telemetry System Setup Script

set -e

echo "🏍️  Setting up Motorcycle Telemetry System"

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "❌ Please run this script as the pi user"
    exit 1
fi

# Make scripts executable
chmod +x motorcycle_telemetry.py
chmod +x data_exporter.py

# Install additional Python packages if needed
echo "📦 Installing additional Python packages..."
source telemetry-env/bin/activate

# Check if packages are installed, install if missing
python -c "import influxdb_client" 2>/dev/null || pip install influxdb-client
python -c "import psutil" 2>/dev/null || pip install psutil

# Test sensors
echo "🧪 Testing sensors..."
python test_imu.py

# Check GPS device
echo "🛰️  Checking GPS device..."
if [ -e "/dev/ttyACM0" ]; then
    echo "✅ GPS device found at /dev/ttyACM0"
elif [ -e "/dev/ttyAMA0" ]; then
    echo "✅ GPS device found at /dev/ttyAMA0"
else
    echo "⚠️  No GPS device found - check connections"
fi

# Create systemd service
echo "⚙️  Setting up systemd service..."
sudo cp motorcycle-telemetry.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable motorcycle-telemetry.service

# Create data directory
mkdir -p /home/pi/motorcycle_data

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/motorcycle-telemetry > /dev/null << EOF
/home/pi/motorcycle_data/telemetry.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 pi pi
    postrotate
        systemctl reload motorcycle-telemetry.service || true
    endscript
}
EOF

# Create calibration script for vibration threshold
echo "🔧 Creating calibration script..."
cat > calibrate_engine_detection.py << 'EOF'
#!/usr/bin/env python3
"""
Calibrate engine detection threshold
Run this with the bike engine on and off to find optimal threshold
"""

import qwiic_icm20948
import time
import sys

def calibrate():
    imu = qwiic_icm20948.QwiicIcm20948()
    
    if not imu.connected:
        print("❌ IMU not detected")
        return
        
    if not imu.begin():
        print("❌ Failed to initialize IMU")
        return
        
    print("🏍️  Engine Detection Calibration")
    print("1. Start with engine OFF, press Enter")
    input()
    
    print("Reading engine OFF values for 10 seconds...")
    off_values = []
    for i in range(100):
        if imu.dataReady():
            imu.getAgmt()
            total = abs(imu.axRaw) + abs(imu.ayRaw) + abs(imu.azRaw)
            off_values.append(total)
        time.sleep(0.1)
    
    off_max = max(off_values)
    off_avg = sum(off_values) / len(off_values)
    
    print(f"Engine OFF - Average: {off_avg:.0f}, Max: {off_max:.0f}")
    
    print("2. Start engine and let it idle, press Enter")
    input()
    
    print("Reading engine ON values for 10 seconds...")
    on_values = []
    for i in range(100):
        if imu.dataReady():
            imu.getAgmt()
            total = abs(imu.axRaw) + abs(imu.ayRaw) + abs(imu.azRaw)
            on_values.append(total)
        time.sleep(0.1)
    
    on_min = min(on_values)
    on_avg = sum(on_values) / len(on_values)
    
    print(f"Engine ON - Average: {on_avg:.0f}, Min: {on_min:.0f}")
    
    # Suggest threshold
    suggested = (off_max + on_min) / 2
    print(f"\n🎯 Suggested threshold: {suggested:.0f}")
    print(f"Current threshold in motorcycle_telemetry.py: 1000")
    print(f"Consider updating VIBRATION_THRESHOLD to {suggested:.0f}")

if __name__ == "__main__":
    calibrate()
EOF

chmod +x calibrate_engine_detection.py

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Connect your buck converter to the bike's 12V system"
echo "2. Run: ./calibrate_engine_detection.py (to optimize engine detection)"
echo "3. Start the service: sudo systemctl start motorcycle-telemetry.service"
echo "4. Check status: sudo systemctl status motorcycle-telemetry.service"
echo "5. View logs: journalctl -fu motorcycle-telemetry.service"
echo ""
echo "🔧 Useful commands:"
echo "- List rides: python data_exporter.py list"
echo "- Export ride: python data_exporter.py export --session <session_id> --format csv"
echo "- Test system: python motorcycle_telemetry.py (Ctrl+C to stop)"
echo ""
echo "🌐 For Grafana integration:"
echo "- Install InfluxDB and configure UPLOAD_URL in motorcycle_telemetry.py"
echo "- Or use CSV exports with Grafana's CSV datasource" 