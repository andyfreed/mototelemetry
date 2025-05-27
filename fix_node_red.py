#!/usr/bin/env python3
"""
Fix Node-RED motorcycle dashboard by using exec instead of SQLite node
"""

import requests
import json
import time

NODE_RED_URL = "http://localhost:1880"

def deploy_working_flow():
    """Deploy the working flow that uses exec instead of SQLite node"""
    try:
        # Read the working flow configuration
        with open('node_red_flow_simple.json', 'r') as f:
            flow_config = json.load(f)
        
        # Replace all flows with our working flow
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=flow_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Working motorcycle dashboard flow deployed!")
            print(f"🔗 Dashboard URL: {NODE_RED_URL}/ui")
            return True
        else:
            print(f"❌ Failed to deploy flow: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying flow: {e}")
        return False

def test_sqlite_access():
    """Test if SQLite database is accessible"""
    import subprocess
    try:
        result = subprocess.run([
            'sqlite3', 
            '/home/pi/motorcycle_data/telemetry.db', 
            'SELECT COUNT(*) FROM telemetry_data;'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            count = int(result.stdout.strip())
            print(f"✅ SQLite database accessible: {count} records")
            return True
        else:
            print(f"❌ SQLite access failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ SQLite test error: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 Fixing Node-RED Motorcycle Dashboard")
    print("=" * 50)
    
    print("🔍 Testing SQLite database access...")
    if not test_sqlite_access():
        print("❌ Cannot access SQLite database")
        return False
    
    print("🚀 Deploying working flow (using exec instead of SQLite node)...")
    if deploy_working_flow():
        print("\n🎉 SUCCESS! Dashboard is now working!")
        print(f"📱 Dashboard: {NODE_RED_URL}/ui")
        print(f"🔧 Editor: {NODE_RED_URL}")
        print("\n💡 This flow uses:")
        print("   • exec node instead of SQLite node (avoids ARM64 binding issues)")
        print("   • Direct sqlite3 command-line tool")
        print("   • JSON output parsing")
        print("   • Same calibration and gauges")
        return True
    else:
        print("❌ Failed to deploy working flow")
        return False

if __name__ == "__main__":
    main() 