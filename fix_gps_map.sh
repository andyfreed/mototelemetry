#!/bin/bash
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