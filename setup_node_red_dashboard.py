#!/usr/bin/env python3
"""
Setup Node-RED motorcycle dashboard by importing the flow configuration
"""

import requests
import json
import time

NODE_RED_URL = "http://localhost:1880"

def wait_for_node_red():
    """Wait for Node-RED to be ready"""
    print("🔄 Waiting for Node-RED to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{NODE_RED_URL}/flows", timeout=5)
            if response.status_code == 200:
                print("✅ Node-RED is ready!")
                return True
        except:
            pass
        time.sleep(2)
        print(f"   Waiting... ({i+1}/30)")
    return False

def import_flow():
    """Import the motorcycle dashboard flow"""
    try:
        # Read the flow configuration
        with open('node_red_flow.json', 'r') as f:
            flow_config = json.load(f)
        
        # Get current flows to avoid overwriting
        response = requests.get(f"{NODE_RED_URL}/flows")
        if response.status_code == 200:
            current_flows = response.json()
        else:
            current_flows = []
        
        # Add our flow to existing flows
        all_flows = current_flows + flow_config
        
        # Import the flow
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=all_flows,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Motorcycle dashboard flow imported successfully!")
            print(f"🔗 Dashboard URL: {NODE_RED_URL}/ui")
            print(f"🔧 Editor URL: {NODE_RED_URL}")
            return True
        else:
            print(f"❌ Failed to import flow: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error importing flow: {e}")
        return False

def main():
    """Main setup function"""
    print("🏍️  Setting up Node-RED Motorcycle Dashboard")
    print("=" * 50)
    
    if not wait_for_node_red():
        print("❌ Node-RED is not responding. Make sure it's running:")
        print("   node-red &")
        return False
    
    if import_flow():
        print("\n🎉 SUCCESS! Your motorcycle dashboard is ready!")
        print(f"📱 Open dashboard: {NODE_RED_URL}/ui")
        print("📊 Features:")
        print("   • Real-time lean angle gauge")
        print("   • Forward & lateral G-force meters")
        print("   • Speed gauge")
        print("   • GPS location map")
        print("   • Updates every 2 seconds")
        print("   • Reads directly from SQLite")
        print("   • Mobile-friendly interface")
        
        print(f"\n🔧 To customize: {NODE_RED_URL}")
        return True
    else:
        return False

if __name__ == "__main__":
    main() 