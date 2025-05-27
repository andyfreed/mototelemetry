#!/usr/bin/env python3
"""
Deploy the GPS-fixed Node-RED motorcycle dashboard
"""

import requests
import json
import time

NODE_RED_URL = "http://localhost:1880"

def deploy_gps_dashboard():
    """Deploy the GPS-fixed dashboard"""
    try:
        # Read the final flow configuration
        with open('node_red_flow_final.json', 'r') as f:
            flow_config = json.load(f)
        
        # Fix the process-data node to properly connect GPS output
        for node in flow_config:
            if node.get('id') == 'process-data':
                # Connect outputs correctly:
                # 0: lean-gauge + data-counter
                # 1: forward-g-gauge
                # 2: lateral-g-gauge  
                # 3: speed-gauge
                # 4: gps-map + gps-forwarder
                node['wires'] = [
                    ["lean-gauge", "data-counter"],
                    ["forward-g-gauge"], 
                    ["lateral-g-gauge"],
                    ["speed-gauge"],
                    ["gps-map", "gps-forwarder"]
                ]
        
        # Replace all flows with our fixed flow
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=flow_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ GPS-fixed motorcycle dashboard deployed!")
            return True
        else:
            print(f"❌ Failed to deploy: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Deploy GPS dashboard"""
    print("🛰️  Deploying GPS-Fixed Motorcycle Dashboard")
    print("=" * 50)
    
    if deploy_gps_dashboard():
        print("\n🎉 GPS DASHBOARD DEPLOYED!")
        print(f"📱 Dashboard: {NODE_RED_URL}/ui")
        print(f"🗺️  GPS Map: {NODE_RED_URL}/worldmap")
        print(f"🔧 Editor: {NODE_RED_URL}")
        
        print("\n✅ GPS FEATURES:")
        print("   • 🗺️ Interactive World Map")
        print("   • 📍 Real-time location tracking")
        print("   • 🛰️ GPS status indicator")
        print("   • 📌 Default location when no GPS")
        print("   • 🏍️ Motorcycle icon on map")
        
        print("\n🔧 GPS ACCESS:")
        print(f"   • Main Dashboard: {NODE_RED_URL}/ui")
        print(f"   • Full-screen Map: {NODE_RED_URL}/worldmap")
        
        print("\n📍 GPS STATUS:")
        print("   • Currently showing: Default location (London)")
        print("   • Reason: GPS coordinates are 0,0 in database")
        print("   • Solution: GPS will show real location when signal acquired")
        
        return True
    else:
        return False

if __name__ == "__main__":
    main() 