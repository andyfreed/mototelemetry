#!/bin/bash
# GPS Fix Script - Resolves GPS connection issues on motorcycle telemetry system

echo "🛰️ GPS FIX SCRIPT"
echo "================="
echo "This script will fix common GPS issues with your motorcycle telemetry system."

# Make sure we're running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo)!"
  exit 1
fi

echo "✅ Running as root, proceeding..."

# Step 1: Check and detect the GPS device
echo -e "\n🔍 DETECTING GPS DEVICE..."
GPS_DEVICES=$(lsusb | grep -i "u-blox\|gps\|1546:")
if [ -z "$GPS_DEVICES" ]; then
  echo "❌ No GPS device detected! Check USB connection."
  exit 1
else
  echo "✅ GPS device detected: $GPS_DEVICES"
fi

# Step 2: Check for serial ports
echo -e "\n🔎 CHECKING SERIAL PORTS..."
POTENTIAL_PORTS=("/dev/ttyACM0" "/dev/ttyACM1" "/dev/ttyUSB0" "/dev/ttyUSB1")
VALID_PORTS=()

for PORT in "${POTENTIAL_PORTS[@]}"; do
  if [ -e "$PORT" ]; then
    VALID_PORTS+=("$PORT")
    echo "✅ Found port: $PORT ($(stat -c %y "$PORT"))"
  else
    echo "❌ Port not found: $PORT"
  fi
done

if [ ${#VALID_PORTS[@]} -eq 0 ]; then
  echo "❌ No valid serial ports found. Check hardware connection!"
  exit 1
fi

# Step 3: Determine the best port to use
if [ ${#VALID_PORTS[@]} -gt 1 ]; then
  echo -e "\n🔍 Multiple ports found, determining best GPS port..."
  GPS_PORT=""
  
  # Try to find a U-Blox device
  for PORT in "${VALID_PORTS[@]}"; do
    if udevadm info --name="$PORT" | grep -q "ID_VENDOR_ID=1546"; then
      echo "✅ Found U-Blox GPS on $PORT"
      GPS_PORT="$PORT"
      break
    fi
  done
  
  # If not found, use the most recently modified port
  if [ -z "$GPS_PORT" ]; then
    NEWEST_PORT=""
    NEWEST_TIME=0
    for PORT in "${VALID_PORTS[@]}"; do
      MOD_TIME=$(stat -c %Y "$PORT")
      if [ "$MOD_TIME" -gt "$NEWEST_TIME" ]; then
        NEWEST_TIME=$MOD_TIME
        NEWEST_PORT=$PORT
      fi
    done
    GPS_PORT=$NEWEST_PORT
    echo "✅ Using most recent port: $GPS_PORT"
  fi
else
  GPS_PORT=${VALID_PORTS[0]}
  echo "✅ Using GPS port: $GPS_PORT"
fi

# Step 4: Stop any existing gpsd instances
echo -e "\n🛑 STOPPING EXISTING GPSD..."
systemctl stop gpsd gpsd.socket
killall -9 gpsd 2>/dev/null
sleep 2
echo "✅ Existing GPSD instances stopped"

# Step 5: Update GPSD configuration
echo -e "\n🔧 UPDATING GPSD CONFIGURATION..."
GPSD_CONFIG="/etc/default/gpsd"

# Create config if doesn't exist
if [ ! -f "$GPSD_CONFIG" ]; then
  echo "Creating new GPSD configuration..."
  cat > "$GPSD_CONFIG" << EOF
# Default settings for the gpsd init script and the hotplug wrapper.

# Start the gpsd daemon automatically at boot time
START_DAEMON="true"

# Use USB hotplugging to add new USB devices automatically to the daemon
USBAUTO="true"

# Devices gpsd should collect to at boot time.
# They need to be read/writeable, either by user gpsd or the group dialout.
DEVICES="$GPS_PORT"

# Other options you want to pass to gpsd
GPSD_OPTIONS="-n"
EOF
else
  # Update existing config
  sed -i "s|^DEVICES=.*|DEVICES=\"$GPS_PORT\"|" "$GPSD_CONFIG"
  sed -i "s|^START_DAEMON=.*|START_DAEMON=\"true\"|" "$GPSD_CONFIG"
  sed -i "s|^GPSD_OPTIONS=.*|GPSD_OPTIONS=\"-n\"|" "$GPSD_CONFIG"
fi

echo "✅ GPSD configuration updated"
cat "$GPSD_CONFIG"

# Step 6: Start GPSD properly
echo -e "\n🚀 STARTING GPSD..."
systemctl start gpsd
sleep 3

# Check if GPSD is running
if systemctl is-active --quiet gpsd; then
  echo "✅ GPSD service started successfully"
else
  echo "⚠️ GPSD service failed to start through systemd"
  echo "Trying direct start..."
  gpsd -n "$GPS_PORT"
  sleep 2
  
  if pgrep -x gpsd > /dev/null; then
    echo "✅ GPSD started manually"
  else
    echo "❌ Failed to start GPSD. Manual troubleshooting required."
    exit 1
  fi
fi

# Step 7: Test GPSD data
echo -e "\n📡 TESTING GPS DATA..."
echo "This will take about 10 seconds..."

GPSPIPE=$(which gpspipe)
if [ -z "$GPSPIPE" ]; then
  echo "⚠️ gpspipe not found, installing..."
  apt-get update && apt-get install -y gpsd-clients
  GPSPIPE=$(which gpspipe)
fi

if [ -n "$GPSPIPE" ]; then
  # Run gpspipe for 10 seconds, capture output
  DATA=$($GPSPIPE -w -n 20 2>/dev/null)
  
  # Check if we got any data
  if [ -n "$DATA" ]; then
    echo "✅ GPS is sending data"
    echo "Sample data:"
    echo "$DATA" | head -n 5
    
    # Check for actual coordinates
    if echo "$DATA" | grep -q '"lat":'; then
      echo "🌍 GPS coordinates detected! GPS is working!"
    else
      echo "⚠️ GPS is sending data but no coordinates yet"
      echo "This is normal for a cold start - GPS needs 1-5 minutes outdoors to get a fix"
    fi
  else
    echo "❌ No data received from GPS"
  fi
else
  echo "❌ Cannot test GPS data - gpspipe not available"
fi

# Step 8: Restart telemetry service
echo -e "\n🔄 RESTARTING MOTORCYCLE TELEMETRY..."
systemctl restart motorcycle-telemetry
if systemctl is-active --quiet motorcycle-telemetry; then
  echo "✅ Telemetry service restarted successfully"
else
  echo "⚠️ Telemetry service is not active"
  echo "Starting it now..."
  systemctl start motorcycle-telemetry
  sleep 2
  
  if systemctl is-active --quiet motorcycle-telemetry; then
    echo "✅ Telemetry service started successfully"
  else
    echo "❌ Failed to start telemetry service"
  fi
fi

# Step 9: Update the Node-RED dashboard IP address
echo -e "\n🔄 UPDATING NODE-RED DASHBOARD CAMERA URL..."
# Get the current IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')
if [ -n "$IP_ADDRESS" ]; then
  echo "✅ Using IP address: $IP_ADDRESS"
  
  # Check if we have the Node-RED flow file
  FLOW_FILE="/home/pi/.node-red/flows.json"
  if [ -f "$FLOW_FILE" ]; then
    # Backup the file
    cp "$FLOW_FILE" "$FLOW_FILE.bak"
    
    # Update the IP address for camera stream
    sed -i "s|http://[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+:8090|http://$IP_ADDRESS:8090|g" "$FLOW_FILE"
    echo "✅ Updated camera URL in Node-RED flows"
    
    # Restart Node-RED to apply changes
    systemctl restart nodered
    echo "✅ Restarted Node-RED service"
  else
    echo "⚠️ Node-RED flow file not found at $FLOW_FILE"
  fi
else
  echo "⚠️ Could not determine IP address"
fi

echo -e "\n🎉 GPS FIX COMPLETE"
echo "===================="
echo "GPS should now be properly configured and running."
echo "If this is a cold start or you're indoors, it may take up to"
echo "5 minutes to acquire a GPS fix. Please be patient."
echo
echo "To monitor GPS status, go to:"
echo "http://$IP_ADDRESS:1880/ui"
echo
echo "If you're still having issues after 5 minutes outdoors,"
echo "check the motorcycle_telemetry.py script for any GPS-specific issues."
echo "You can also run: gpspipe -w to see raw GPS data stream." 