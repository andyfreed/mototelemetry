#!/usr/bin/env python3
"""
Restore the full motorcycle dashboard and update map location to Massachusetts
"""

import requests
import json
import sys

NODE_RED_URL = "http://localhost:1880"

def restore_dashboard():
    """Restore the full dashboard with gauges and correct map location"""
    try:
        # Load the enhanced flow with camera
        with open('enhanced_node_red_flow_with_camera.json', 'r') as f:
            dashboard_flow = json.load(f)
        
        # Update all worldmap nodes to use Massachusetts coordinates
        for node in dashboard_flow:
            if node.get('type') == 'worldmap':
                # Boston, Massachusetts coordinates
                node['lat'] = "42.3601"
                node['lon'] = "-71.0589"
                node['layer'] = "OSM"  # Use OpenStreetMap for better detail
                node['maplist'] = "OSMG,OSMC,EsriC,EsriS,EsriT,EsriDG,UKOS"
                print(f"✅ Updated map location for node: {node.get('id')}")
        
        # Deploy the full restored flow
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=dashboard_flow,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in [200, 204]:
            print(f"❌ Failed to deploy: {response.status_code} - {response.text}")
            return False
        
        print("✅ Successfully restored dashboard!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🏍️ Restoring full motorcycle dashboard...")
    if restore_dashboard():
        print("\n🎉 DASHBOARD RESTORED SUCCESSFULLY!")
        print("All gauges should now be visible again and the map location")
        print("has been updated to Massachusetts instead of London.")
        print("\n📍 NEW DEFAULT LOCATION: Boston, Massachusetts")
        print("   The map will show your actual location once GPS has a fix.")
        
        print("\n🚀 Access your dashboard at: http://localhost:1880/ui")
    else:
        sys.exit(1) 