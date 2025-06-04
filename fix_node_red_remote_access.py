#!/usr/bin/env python3
"""
Fix Node-RED Remote Access
Updates hardcoded IP addresses in Node-RED flows to use dynamic hostnames
"""

import json
import requests
import sys

def get_flows():
    """Get current Node-RED flows"""
    try:
        response = requests.get('http://127.0.0.1:1880/flows')
        return response.json()
    except Exception as e:
        print(f"Error getting flows: {e}")
        return None

def update_flows(flows):
    """Update flows to replace hardcoded IPs with dynamic hostnames"""
    updated = False
    
    for flow in flows:
        if flow.get('type') == 'ui_template':
            format_content = flow.get('format', '')
            
            # Replace hardcoded camera IP with dynamic hostname
            if '10.0.0.155:8090' in format_content:
                print(f"Updating camera URLs in: {flow.get('name', 'Unknown')}")
                
                # Replace camera stream URL
                format_content = format_content.replace(
                    'http://10.0.0.155:8090/stream.mjpg',
                    'http://" + window.location.hostname + ":8090/stream.mjpg'
                )
                
                # Replace snapshot URL
                format_content = format_content.replace(
                    'http://10.0.0.155:8090/snapshot',
                    'http://" + window.location.hostname + ":8090/snapshot'
                )
                
                flow['format'] = format_content
                updated = True
                
    return flows if updated else None

def deploy_flows(flows):
    """Deploy updated flows to Node-RED"""
    try:
        response = requests.post(
            'http://127.0.0.1:1880/flows',
            json=flows,
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error deploying flows: {e}")
        return False

def main():
    print("🔧 Fixing Node-RED Remote Access...")
    
    # Get current flows
    print("📥 Getting current flows...")
    flows = get_flows()
    if not flows:
        print("❌ Failed to get flows")
        sys.exit(1)
    
    # Update flows
    print("🔄 Updating hardcoded IPs...")
    updated_flows = update_flows(flows)
    
    if not updated_flows:
        print("✅ No updates needed - flows already use dynamic hostnames")
        return
    
    # Deploy updated flows
    print("🚀 Deploying updated flows...")
    if deploy_flows(updated_flows):
        print("✅ Successfully updated Node-RED flows for remote access!")
        print("📱 Camera feed and APIs will now work via Tailscale")
        print("🌐 Remote access: http://100.119.155.66:1880/ui")
    else:
        print("❌ Failed to deploy updated flows")
        sys.exit(1)

if __name__ == "__main__":
    main() 