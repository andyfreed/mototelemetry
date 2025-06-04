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
