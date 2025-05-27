#!/bin/bash
# Fix network routing for motorcycle telemetry system
# This ensures internet connectivity for map tiles

echo "🌐 FIXING NETWORK CONNECTIVITY FOR GPS MAPS"
echo "============================================="

# Check current routing
echo "📍 Current routing:"
ip route show | grep default

# Test connectivity
echo "🔍 Testing internet connectivity..."
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ Internet connectivity already working"
else
    echo "⚠️  Internet connectivity issue detected"
    echo "🔧 Fixing routing..."
    
    # Remove problematic USB route if it exists
    if ip route show | grep -q "default via 192.168.225.1 dev usb0"; then
        echo "🗑️  Removing problematic USB default route..."
        sudo ip route del default via 192.168.225.1 dev usb0
    fi
    
    # Ensure WiFi route exists
    if ! ip route show | grep -q "default via.*wlan0"; then
        echo "🛜 Adding WiFi default route..."
        sudo ip route add default via 10.0.0.1 dev wlan0 metric 600
    fi
    
    # Test again
    if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
        echo "✅ Internet connectivity restored!"
    else
        echo "❌ Still having connectivity issues"
        echo "📋 Current routes:"
        ip route show
        exit 1
    fi
fi

# Test map tile access
echo "🗺️  Testing map tile server access..."
if curl -s -I "https://tile.openstreetmap.org/15/10691/12284.png" | grep -q "200"; then
    echo "✅ Map tile servers accessible"
else
    echo "❌ Cannot reach map tile servers"
    exit 1
fi

echo "🎉 Network connectivity fixed! GPS maps should now work."
echo "📱 Dashboard: http://localhost:1880/ui"
echo "🗺️ GPS Map: http://localhost:1880/worldmap" 