#!/bin/bash
# Motorcycle Telemetry System - Startup Verification
# Checks all services and their auto-start configuration

echo "🏍️ Motorcycle Telemetry System - Startup Check"
echo "=============================================="
date
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service status
check_service() {
    local service=$1
    local description=$2
    
    # Check if service is active
    if systemctl is-active --quiet $service; then
        status="${GREEN}✅ Running${NC}"
    else
        status="${RED}❌ Stopped${NC}"
    fi
    
    # Check if service is enabled
    if systemctl is-enabled --quiet $service 2>/dev/null; then
        enabled="${GREEN}Auto-start: ON${NC}"
    else
        enabled="${YELLOW}Auto-start: OFF${NC}"
    fi
    
    printf "%-35s %s | %s\n" "$description" "$status" "$enabled"
}

# Function to check temperature
check_temperature() {
    temp=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1)
    temp_num=$(echo $temp | cut -d'.' -f1)
    
    if [ $temp_num -lt 60 ]; then
        temp_color="${GREEN}"
        temp_status="🟢 Excellent"
    elif [ $temp_num -lt 70 ]; then
        temp_color="${BLUE}"
        temp_status="🟡 Good"
    elif [ $temp_num -lt 80 ]; then
        temp_color="${YELLOW}"
        temp_status="🟠 Warm"
    else
        temp_color="${RED}"
        temp_status="🔴 Hot"
    fi
    
    echo -e "🌡️  CPU Temperature: ${temp_color}${temp}°C${NC} | $temp_status"
}

echo "📊 SYSTEM STATUS:"
echo "=================="

# Check temperature
check_temperature

# Get load average
load_avg=$(cat /proc/loadavg | cut -d' ' -f1)
echo "⚡ CPU Load Average: $load_avg"

# Get memory usage
mem_info=$(free -h | grep '^Mem:')
mem_used=$(echo $mem_info | awk '{print $3}')
mem_total=$(echo $mem_info | awk '{print $2}')
echo "💾 Memory Usage: $mem_used / $mem_total"

echo ""
echo "🚀 SERVICE STATUS:"
echo "=================="

# Core services
check_service "motorcycle-telemetry.service" "🏍️  Motorcycle Telemetry"
check_service "nodered.service" "📊 Node-RED Dashboard"
check_service "camera-stream.service" "📹 Camera Stream"
check_service "tailscaled.service" "🔒 Tailscale VPN"

echo ""
echo "📡 CONNECTIVITY:"
echo "================"
check_service "ModemManager.service" "📱 Cellular Modem Manager"
check_service "wpa_supplicant.service" "📶 WiFi Connection"

echo ""
echo "🛰️ GPS STATUS:"
echo "=============="
# Check cellular GPS
gps_status=$(sudo mmcli -m 0 --location-status 2>/dev/null | grep "enabled:" | awk '{print $3}')
if [[ "$gps_status" == *"gps-nmea"* ]]; then
    echo -e "📍 Cellular GPS: ${GREEN}✅ Enabled${NC}"
else
    echo -e "📍 Cellular GPS: ${RED}❌ Disabled${NC}"
fi

# Check for GPS fix
gps_data=$(sudo mmcli -m 0 --location-get 2>/dev/null | grep -A5 "GPS")
if echo "$gps_data" | grep -q "\$GPRMC.*,A,"; then
    echo -e "🛰️  GPS Fix: ${GREEN}✅ Active${NC}"
else
    echo -e "🛰️  GPS Fix: ${YELLOW}⏳ Searching${NC}"
fi

echo ""
echo "🌐 NETWORK ACCESS:"
echo "=================="

# Check local interfaces
echo "🏠 Local Access:"
ip_wifi=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \K\S+' | head -1)
if [ ! -z "$ip_wifi" ]; then
    echo "   WiFi IP: http://$ip_wifi:1880/ui (Node-RED)"
    echo "   Camera:  http://$ip_wifi:8090"
fi

# Check Tailscale
tailscale_ip=$(tailscale ip 2>/dev/null)
if [ ! -z "$tailscale_ip" ]; then
    echo -e "🔒 Remote Access (Tailscale): ${GREEN}✅ Connected${NC}"
    echo "   Dashboard: http://$tailscale_ip:1880/ui"
    echo "   Camera:    http://$tailscale_ip:8090"
else
    echo -e "🔒 Remote Access (Tailscale): ${RED}❌ Disconnected${NC}"
fi

# Check cellular
cellular_ip=$(ip addr show wwan0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d'/' -f1)
if [ ! -z "$cellular_ip" ]; then
    echo -e "📱 Cellular Connection: ${GREEN}✅ Connected${NC} ($cellular_ip)"
else
    echo -e "📱 Cellular Connection: ${YELLOW}⏳ Connecting${NC}"
fi

echo ""
echo "📋 QUICK ACCESS URLs:"
echo "===================="
echo "🎛️  Node-RED Dashboard:"
if [ ! -z "$tailscale_ip" ]; then
    echo "   Remote: http://$tailscale_ip:1880/ui"
fi
if [ ! -z "$ip_wifi" ]; then
    echo "   Local:  http://$ip_wifi:1880/ui"
fi

echo "📹 Camera Feed:"
if [ ! -z "$tailscale_ip" ]; then
    echo "   Remote: http://$tailscale_ip:8090"
fi
if [ ! -z "$ip_wifi" ]; then
    echo "   Local:  http://$ip_wifi:8090"
fi

echo ""
echo "🔧 TROUBLESHOOTING:"
echo "==================="
echo "Temperature Monitor: python3 temp_monitor.py"
echo "GPS Test:           python3 cellular_gps.py"
echo "Service Restart:    sudo systemctl restart <service-name>"
echo "View Logs:          journalctl -u <service-name> -f"

echo ""
echo "✅ Status check complete!" 