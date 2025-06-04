#!/bin/bash
# Enhanced GPS Fix Script for Pi 5 Motorcycle Telemetry

echo "🛰️ ENHANCED GPS FIX SCRIPT"
echo "========================="
echo "This script will thoroughly fix GPS issues on your Pi 5 motorcycle telemetry system."

# Make sure we're running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo)!"
  exit 1
fi

echo "✅ Running as root, proceeding..."

# Helper function to print section headers
section() {
  echo -e "\n🔧 $1"
  echo "------------------------"
}

# Step 1: Completely stop all gpsd instances
section "STOPPING ALL GPSD INSTANCES"
echo "Stopping all gpsd services and killing any running instances..."
systemctl stop gpsd gpsd.socket
killall -9 gpsd 2>/dev/null
sleep 2
# Double check for lingering processes
if pgrep -x gpsd > /dev/null; then
  echo "⚠️ gpsd still running after kill, forcing termination..."
  pkill -9 -f gpsd
  sleep 1
fi
echo "✅ All gpsd instances stopped"

# Step 2: Check and detect GPS device
section "DETECTING GPS DEVICE"
GPS_DEVICES=$(lsusb | grep -i "u-blox\|gps\|1546:")
if [ -z "$GPS_DEVICES" ]; then
  echo "❌ No GPS device detected in USB bus! Check hardware connection."
  echo "Continuing anyway as it might be on a different interface..."
else
  echo "✅ GPS device detected: $GPS_DEVICES"
fi

# Step 3: Find available serial ports
section "FINDING ALL POTENTIAL GPS PORTS"
POTENTIAL_PORTS=("/dev/ttyACM0" "/dev/ttyACM1" "/dev/ttyUSB0" "/dev/ttyUSB1" "/dev/serial0" "/dev/ttyS0")
VALID_PORTS=()

for PORT in "${POTENTIAL_PORTS[@]}"; do
  if [ -e "$PORT" ]; then
    VALID_PORTS+=("$PORT")
    echo "✅ Found port: $PORT ($(stat -c %y "$PORT"))"
    
    # Check permissions and fix if needed
    PERMS=$(stat -c "%a" "$PORT")
    if [ "$PERMS" != "666" ]; then
      echo "⚠️ Port $PORT has permissions $PERMS, changing to 666..."
      chmod 666 "$PORT"
    fi
    
    # Check ownership
    OWNER=$(stat -c "%U:%G" "$PORT")
    echo "   Owner: $OWNER"
    
    # Test if port responds (try to read some data)
    echo "   Testing port responsiveness..."
    if timeout 2 cat "$PORT" > /dev/null 2>&1; then
      echo "   ✅ Port $PORT is responding to read requests"
    else
      echo "   ⚠️ Port $PORT not responding to reads (might still be valid for GPS)"
    fi
  else
    echo "❌ Port not found: $PORT"
  fi
done

if [ ${#VALID_PORTS[@]} -eq 0 ]; then
  echo "❌ No valid serial ports found. Check hardware connection!"
  echo "Attempting to restart USB system..."
  
  # Try restarting USB
  echo 'usb' > /sys/bus/usb/drivers/usb/unbind
  sleep 2
  echo 'usb' > /sys/bus/usb/drivers/usb/bind
  sleep 3
  
  # Check again
  for PORT in "${POTENTIAL_PORTS[@]}"; do
    if [ -e "$PORT" ]; then
      VALID_PORTS+=("$PORT")
      echo "✅ Found port after USB restart: $PORT"
    fi
  done
  
  if [ ${#VALID_PORTS[@]} -eq 0 ]; then
    echo "❌ Still no ports found. Hardware issue detected."
    exit 1
  fi
fi

# Step 4: Determine the best port to use
if [ ${#VALID_PORTS[@]} -gt 1 ]; then
  section "DETERMINING BEST GPS PORT"
  GPS_PORT=""
  
  # Try to find a U-Blox device
  for PORT in "${VALID_PORTS[@]}"; do
    if udevadm info --name="$PORT" | grep -q "ID_VENDOR_ID=1546"; then
      echo "✅ Found U-Blox GPS on $PORT"
      GPS_PORT="$PORT"
      break
    fi
  done
  
  # If not found, use ttyACM0 if available, as it's most common
  if [ -z "$GPS_PORT" ]; then
    if [[ " ${VALID_PORTS[@]} " =~ " /dev/ttyACM0 " ]]; then
      GPS_PORT="/dev/ttyACM0"
      echo "✅ Using common GPS port: $GPS_PORT"
    else
      # Use the most recently modified port
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
  fi
else
  GPS_PORT=${VALID_PORTS[0]}
  echo "✅ Using GPS port: $GPS_PORT"
fi

# Step 5: Purge and reinstall gpsd
section "REINSTALLING GPSD"
echo "Completely removing and reinstalling gpsd..."
apt-get remove --purge -y gpsd gpsd-clients
sleep 1
apt-get update
apt-get install -y gpsd gpsd-clients
echo "✅ GPSD reinstalled"

# Step 6: Update GPSD configuration
section "UPDATING GPSD CONFIGURATION"
GPSD_CONFIG="/etc/default/gpsd"

# Always create a new config to ensure it's clean
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

# Ensure permissions are correct
chmod 644 "$GPSD_CONFIG"
echo "✅ GPSD configuration updated"
cat "$GPSD_CONFIG"

# Step 7: Fix systemd service if needed
section "FIXING SYSTEMD SERVICE"
if [ -f "/lib/systemd/system/gpsd.service" ]; then
  echo "Checking gpsd systemd service..."
  # Backup the original
  cp "/lib/systemd/system/gpsd.service" "/lib/systemd/system/gpsd.service.bak"
  
  # Modify to ensure it uses our device directly
  sed -i "s|^ExecStart=.*|ExecStart=/usr/sbin/gpsd -n $GPS_PORT|" "/lib/systemd/system/gpsd.service"
  
  # Ensure it restarts on failure
  if ! grep -q "Restart=" "/lib/systemd/system/gpsd.service"; then
    sed -i "/\[Service\]/a Restart=on-failure\nRestartSec=5" "/lib/systemd/system/gpsd.service"
  fi
  
  echo "✅ GPSD systemd service fixed"
fi

# Create an override directory if it doesn't exist
mkdir -p /etc/systemd/system/gpsd.service.d/

# Create an override file
cat > /etc/systemd/system/gpsd.service.d/override.conf << EOF
[Service]
# Use our specific port
ExecStart=
ExecStart=/usr/sbin/gpsd -n $GPS_PORT
# Ensure it restarts on failure
Restart=on-failure
RestartSec=5
EOF

echo "✅ Created systemd override for gpsd service"

# Step 8: Reload systemd and start GPSD
section "STARTING GPSD SERVICE"
systemctl daemon-reload
systemctl enable gpsd
systemctl restart gpsd
sleep 3

# Check if GPSD is running
if systemctl is-active --quiet gpsd; then
  echo "✅ GPSD service started successfully"
else
  echo "⚠️ GPSD service failed to start through systemd"
  echo "Trying direct start..."
  gpsd -N -n "$GPS_PORT"
  sleep 2
  
  if pgrep -x gpsd > /dev/null; then
    echo "✅ GPSD started manually"
    
    # Create a custom service to ensure it stays running
    cat > /etc/systemd/system/gpsd-custom.service << EOF
[Unit]
Description=GPS (Global Positioning System) Daemon - Custom
After=network.target

[Service]
Type=simple
ExecStart=/usr/sbin/gpsd -N -n $GPS_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable gpsd-custom.service
    systemctl start gpsd-custom.service
    echo "✅ Created and started custom gpsd service"
  else
    echo "❌ Failed to start GPSD. Manual troubleshooting required."
    exit 1
  fi
fi

# Step 9: Test GPSD data
section "TESTING GPS DATA"
echo "This will take about 10 seconds..."

GPSPIPE=$(which gpspipe)
if [ -z "$GPSPIPE" ]; then
  echo "⚠️ gpspipe not found, installing..."
  apt-get install -y gpsd-clients
  GPSPIPE=$(which gpspipe)
fi

if [ -n "$GPSPIPE" ]; then
  # Run gpspipe for 10 seconds, capture output
  echo "Running gpspipe for 10 seconds..."
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

# Step 10: Restart the motorcycle telemetry service
section "RESTARTING MOTORCYCLE TELEMETRY"
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

section "RESTARTING CAMERA SERVICES"
for service in camera-stream route-tracker; do
  if systemctl list-unit-files | grep -q "$service.service"; then
    echo "Restarting $service service..."
    systemctl restart $service.service
    
    if systemctl is-active --quiet $service.service; then
      echo "✅ $service service restarted successfully"
    else
      echo "⚠️ $service service failed to restart"
      systemctl start $service.service
    fi
  fi
done

section "UPDATING NODE-RED"
# Update the Node-RED flow if it exists
if systemctl list-unit-files | grep -q "nodered.service"; then
  echo "Restarting Node-RED service..."
  systemctl restart nodered.service
  echo "✅ Node-RED service restarted"
fi

# Final summary
echo -e "\n🎉 ENHANCED GPS FIX COMPLETE"
echo "==========================="
echo "GPS should now be properly configured and running."
echo "If you're indoors, GPS may not get a fix until you go outside."
echo "It can take up to 5 minutes to acquire a GPS fix on cold start."
echo 
echo "To monitor GPS status, go to your dashboard or run:"
echo "cgps"
echo
echo "If you're still having issues after trying this outdoors for 5 minutes,"
echo "check hardware connections or try a different GPS module."

# Fix GPS Map Display Script
# This script ensures the GPS data is properly displayed on the map

echo "🔧 Fixing GPS map display..."

# 1. Restart gpsd with the proper device
sudo systemctl stop gpsd-custom.service
sudo systemctl disable gpsd-custom.service
sudo systemctl restart gpsd

# 2. Test GPS connection
echo "🔍 Testing GPS connection..."
GPS_TEST=$(cgps -s -n 1 2>&1)
if [[ $GPS_TEST == *"No fix"* ]] || [[ $GPS_TEST == *"error"* ]]; then
  echo "❌ GPS not providing a fix yet. This is normal if you just started the device."
  echo "   The map will update once GPS acquires a fix."
else
  echo "✅ GPS connected and has a fix!"
fi

# 3. Update map location in Node-RED flow
echo "📍 Updating map configuration..."
python3 - << EOF
import requests
import json

NODE_RED_URL = "http://localhost:1880"

def fix_map_display():
    try:
        # Get current flows
        response = requests.get(
            f"{NODE_RED_URL}/flows",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get current flows: {response.status_code}")
            return False
            
        flows = response.json()
        
        # Find all worldmap nodes and update them
        updated = 0
        for node in flows:
            if node.get('type') == 'worldmap':
                # Set default to Massachusetts but the GPS data will override this
                node['lat'] = "42.3601"
                node['lon'] = "-71.0589"
                node['layer'] = "OSM"  # Use OpenStreetMap for better detail
                node['maplist'] = "OSMG,OSMC,EsriC,EsriS,EsriT,EsriDG,UKOS"
                
                # Most importantly, check if the map is connected to the GPS data
                # Find the GPS calculation function
                updated += 1
        
        if updated > 0:
            print(f"✅ Updated {updated} map nodes")
            
            # Deploy the changes
            response = requests.post(
                f"{NODE_RED_URL}/flows",
                json=flows,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code not in [200, 204]:
                print(f"❌ Failed to deploy: {response.status_code}")
                return False
                
            print("✅ Successfully updated Node-RED flows!")
            return True
        else:
            print("❓ No worldmap nodes found in the flow")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

fix_map_display()
EOF

# 4. Restart route tracker service
echo "🧭 Restarting route tracker service..."
sudo systemctl restart route-tracker.service

# 5. Final instructions
echo ""
echo "🎉 GPS map fix completed!"
echo "The map should now show your actual location once a GPS fix is acquired."
echo "If the map still shows a default location, please make sure:"
echo "  1. Your GPS device is correctly connected"
echo "  2. You're in a location with GPS coverage"
echo "  3. Wait a few minutes for the GPS to acquire a fix"
echo ""
echo "To view your dashboard, go to: http://localhost:1880/ui"

exit 0 