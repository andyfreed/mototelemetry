#!/usr/bin/env python3
"""
Deploy Node-RED motorcycle dashboard with embedded GPS map
"""

import requests
import json
import time

NODE_RED_URL = "http://localhost:1880"

def deploy_map_dashboard():
    """Deploy the dashboard with embedded map"""
    try:
        # Read the map widget flow configuration
        with open('node_red_flow_with_map_widget.json', 'r') as f:
            flow_config = json.load(f)
        
        # Fix the process-data node connections
        for node in flow_config:
            if node.get('id') == 'process-data':
                # Connect all outputs correctly
                node['wires'] = [
                    ["lean-gauge", "data-counter"],
                    ["forward-g-gauge"], 
                    ["lateral-g-gauge"],
                    ["speed-gauge"],
                    ["gps-map", "gps-forwarder"],
                    ["map-widget"]
                ]
        
        # Deploy the flow
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=flow_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Dashboard with embedded GPS map deployed!")
            return True
        else:
            print(f"❌ Failed to deploy: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Deploy map dashboard"""
    print("🗺️  Deploying Dashboard with Embedded GPS Map")
    print("=" * 50)
    
    if deploy_map_dashboard():
        print("\n🎉 DASHBOARD WITH MAP DEPLOYED!")
        print(f"📱 Dashboard: {NODE_RED_URL}/ui")
        print(f"🗺️  Full Map: {NODE_RED_URL}/worldmap")
        
        print("\n✅ NEW FEATURES:")
        print("   • 🗺️ GPS Map Widget - Now embedded in dashboard!")
        print("   • 📍 Shows default location (London) when no GPS")
        print("   • 🏍️ Will show motorcycle position when GPS active")
        print("   • 📱 Mobile-responsive map view")
        
        print("\n📍 WHAT YOU'LL SEE:")
        print("   • Map widget in the '🗺️ GPS Map' section")
        print("   • Default location (London) until GPS gets signal")
        print("   • Red marker = No GPS, Blue marker = Active GPS")
        
        print("\n🔧 TROUBLESHOOTING GPS:")
        print("   • Unplug/replug GPS puck as planned")
        print("   • Move outdoors for better signal")
        print("   • Wait 2-3 minutes for satellite acquisition")
        
        print(f"\n🚀 Access your dashboard: {NODE_RED_URL}/ui")
        print("   Look for the new '🗺️ GPS Map' section!")
        return True
    else:
        return False

if __name__ == "__main__":
    main() 