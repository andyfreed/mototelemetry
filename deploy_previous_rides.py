#!/usr/bin/env python3
"""
Deploy Previous Rides Dashboard
Adds a historical rides view to the dashboard with map visualization
"""

import requests
import json
import time

NODE_RED_URL = "http://localhost:1880"

def deploy_previous_rides_dashboard():
    """Deploy the dashboard with previous rides viewer"""
    try:
        # Read the current flow configuration
        response = requests.get(
            f"{NODE_RED_URL}/flows",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get current flows: {response.status_code}")
            return False
            
        current_flows = response.json()
        
        # Find the motorcycle dashboard tab
        dashboard_tab = None
        # The response might be a list directly, not a dict with a 'flows' key
        flows_data = current_flows if isinstance(current_flows, list) else current_flows.get('flows', [])
        
        for flow in flows_data:
            if flow.get('type') == 'tab' and '🏍️ Motorcycle Dashboard' in flow.get('label', ''):
                dashboard_tab = flow
                break
        
        if not dashboard_tab:
            print("❌ Could not find motorcycle dashboard tab")
            return False
        
        # Create new UI group for previous rides
        previous_rides_group = {
            "id": "previous-rides-group",
            "type": "ui_group",
            "name": "📜 Previous Rides",
            "tab": "dashboard-tab",
            "order": 4,
            "disp": True,
            "width": 12,
            "collapse": False,
            "className": ""
        }
        
        # Create new UI tab for previous rides if needed
        ride_history_tab = {
            "id": "ride-history-tab",
            "type": "ui_tab",
            "name": "📜 Ride History",
            "icon": "motorcycle",
            "order": 2,
            "disabled": False,
            "hidden": False
        }
        
        # Create new UI group for ride history
        ride_history_group = {
            "id": "ride-history-group",
            "type": "ui_group",
            "name": "Previous Rides",
            "tab": "ride-history-tab",
            "order": 1,
            "disp": True,
            "width": 12,
            "collapse": False,
            "className": ""
        }
        
        # Create nodes for the previous rides feature
        previous_rides_nodes = [
            # Ride History Tab
            ride_history_tab,
            ride_history_group,
            
            # Inject node to get list of rides
            {
                "id": "inject-rides-list",
                "type": "inject",
                "z": dashboard_tab['id'],
                "name": "Every 10 seconds",
                "props": [{"p": "payload"}],
                "repeat": "10",
                "crontab": "",
                "once": True,
                "onceDelay": 1,
                "topic": "",
                "payload": "",
                "payloadType": "date",
                "x": 140,
                "y": 500,
                "wires": [["get-rides-list"]]
            },
            
            # HTTP request to get rides list
            {
                "id": "get-rides-list",
                "type": "http request",
                "z": dashboard_tab['id'],
                "name": "Get Rides List",
                "method": "GET",
                "ret": "obj",
                "paytoqs": "ignore",
                "url": "http://localhost:5000/api/rides",
                "tls": "",
                "persist": False,
                "proxy": "",
                "authType": "",
                "x": 320,
                "y": 500,
                "wires": [["format-rides-list"]]
            },
            
            # Format rides list for dropdown
            {
                "id": "format-rides-list",
                "type": "function",
                "z": dashboard_tab['id'],
                "name": "Format Rides List",
                "func": """
if (msg.payload && msg.payload.rides) {
    const rides = msg.payload.rides;
    
    // Format for dropdown
    const formattedRides = rides.map(ride => {
        const startTime = new Date(ride.start_time).toLocaleString();
        const distance = ride.distance_miles ? 
            ride.distance_miles.toFixed(1) + ' mi' : 'Unknown';
        const name = ride.name || `Ride on ${startTime}`;
        
        return {
            value: ride.ride_id,
            label: `${name} (${distance}) - ${startTime}`
        };
    });
    
    // Send to dropdown
    const dropdown = { payload: formattedRides };
    
    // Store full ride data for later use
    flow.set('allRides', rides);
    
    return dropdown;
}
return null;
                """,
                "outputs": 1,
                "noerr": 0,
                "initialize": "",
                "finalize": "",
                "libs": [],
                "x": 500,
                "y": 500,
                "wires": [["rides-dropdown"]]
            },
            
            # Dropdown for selecting previous rides
            {
                "id": "rides-dropdown",
                "type": "ui_dropdown",
                "z": dashboard_tab['id'],
                "name": "Previous Rides",
                "label": "🏍️ Select a Previous Ride",
                "tooltip": "",
                "place": "Select a ride to view",
                "group": "previous-rides-group",
                "order": 1,
                "width": 0,
                "height": 0,
                "passthru": True,
                "multiple": False,
                "options": [],
                "payload": "",
                "topic": "ride_id",
                "topicType": "str",
                "className": "",
                "x": 680,
                "y": 500,
                "wires": [["get-ride-track"]]
            },
            
            # HTTP request to get ride track
            {
                "id": "get-ride-track",
                "type": "http request",
                "z": dashboard_tab['id'],
                "name": "Get Ride Track",
                "method": "GET",
                "ret": "obj",
                "paytoqs": "ignore",
                "url": "http://localhost:5000/api/ride/{{payload}}/geojson",
                "tls": "",
                "persist": False,
                "proxy": "",
                "authType": "",
                "x": 340,
                "y": 560,
                "wires": [["prepare-ride-display"]]
            },
            
            # Function to prepare ride data for display
            {
                "id": "prepare-ride-display",
                "type": "function",
                "z": dashboard_tab['id'],
                "name": "Prepare Ride Display",
                "func": """
if (msg.payload && msg.payload.geojson) {
    // Get the ride details from stored data
    const rides = flow.get('allRides') || [];
    const ride = rides.find(r => r.ride_id === msg.topic);
    
    if (!ride) return null;
    
    // Format for map
    const mapData = {
        payload: msg.payload.geojson,
        name: ride.name || 'Previous Ride',
        center: true
    };
    
    // Format for ride info
    const startTime = new Date(ride.start_time).toLocaleString();
    const endTime = ride.end_time ? new Date(ride.end_time).toLocaleString() : 'In Progress';
    const distance = ride.distance_miles ? ride.distance_miles.toFixed(2) + ' miles' : 'Unknown';
    const maxSpeed = ride.max_speed_mph ? ride.max_speed_mph.toFixed(1) + ' mph' : 'Unknown';
    const avgSpeed = ride.avg_speed_mph ? ride.avg_speed_mph.toFixed(1) + ' mph' : 'Unknown';
    
    const rideInfo = {
        payload: `
<div style="padding: 10px; background: #f5f5f5; border-radius: 5px; margin-bottom: 10px;">
  <h3 style="margin-top: 0;">${ride.name || 'Ride Details'}</h3>
  <p><strong>Start:</strong> ${startTime}</p>
  <p><strong>End:</strong> ${endTime}</p>
  <p><strong>Distance:</strong> ${distance}</p>
  <p><strong>Max Speed:</strong> ${maxSpeed}</p>
  <p><strong>Avg Speed:</strong> ${avgSpeed}</p>
</div>
        `
    };
    
    return [mapData, rideInfo];
}
return [null, null];
                """,
                "outputs": 2,
                "noerr": 0,
                "initialize": "",
                "finalize": "",
                "libs": [],
                "x": 540,
                "y": 560,
                "wires": [["previous-ride-map"], ["ride-info-display"]]
            },
            
            # Map to display previous ride
            {
                "id": "previous-ride-map",
                "type": "ui_worldmap",
                "z": dashboard_tab['id'],
                "name": "Previous Ride Map",
                "group": "ride-history-group",
                "order": 2,
                "width": 12,
                "height": 8,
                "lat": "51.05",
                "lon": "-1.35",
                "zoom": "13",
                "layer": "OSM",
                "cluster": "",
                "maxage": "",
                "usermenu": "show",
                "layers": "show",
                "panit": "false",
                "panlock": "false",
                "zoomlock": "false",
                "hiderightclick": "false",
                "coords": "deg",
                "showgrid": "false",
                "allowFileDrop": "false",
                "path": "/worldmap",
                "overlist": "DR,CO,RA,DN,HM",
                "maplist": "OSMG,OSMC,EsriC,EsriS,EsriT,EsriDG,UKOS",
                "mapname": "",
                "mapurl": "",
                "mapopt": "",
                "mapwms": false,
                "x": 750,
                "y": 540,
                "wires": []
            },
            
            # HTML display for ride info
            {
                "id": "ride-info-display",
                "type": "ui_template",
                "z": dashboard_tab['id'],
                "name": "Ride Info",
                "group": "ride-history-group",
                "order": 1,
                "width": 12,
                "height": 5,
                "format": "<div ng-bind-html=\"msg.payload\"></div>",
                "storeOutMessages": True,
                "fwdInMessages": True,
                "resendOnRefresh": True,
                "templateScope": "local",
                "className": "",
                "x": 750,
                "y": 580,
                "wires": [[]]
            },
            
            # Button to view previous rides
            {
                "id": "view-rides-button",
                "type": "ui_button",
                "z": dashboard_tab['id'],
                "name": "View Previous Rides",
                "group": "previous-rides-group",
                "order": 2,
                "width": 0,
                "height": 0,
                "passthru": False,
                "label": "📜 View Previous Rides",
                "tooltip": "",
                "color": "",
                "bgcolor": "",
                "className": "",
                "icon": "",
                "payload": "",
                "payloadType": "str",
                "topic": "topic",
                "topicType": "str",
                "x": 680,
                "y": 440,
                "wires": [["navigate-to-rides"]]
            },
            
            # Function to navigate to rides tab
            {
                "id": "navigate-to-rides",
                "type": "ui_ui_control",
                "z": dashboard_tab['id'],
                "name": "Navigate to Rides Tab",
                "events": "all",
                "x": 900,
                "y": 440,
                "wires": [[]]
            }
        ]
        
        # Add previous rides group to existing config
        existing_groups = False
        
        # The response might be a list directly, not a dict with a 'flows' key
        flows_list = current_flows if isinstance(current_flows, list) else current_flows.get('flows', [])
        
        for node in flows_list:
            if node.get('id') == previous_rides_group['id']:
                existing_groups = True
                break
        
        if not existing_groups:
            flows_list.append(previous_rides_group)
        
        # Add new nodes to the flow
        for node in previous_rides_nodes:
            # Check if node already exists
            exists = False
            for i, existing_node in enumerate(flows_list):
                if existing_node.get('id') == node['id']:
                    # Update existing node
                    flows_list[i] = node
                    exists = True
                    break
            
            if not exists:
                flows_list.append(node)
        
        # Update the flows if needed
        if isinstance(current_flows, dict) and 'flows' in current_flows:
            current_flows['flows'] = flows_list
        else:
            current_flows = flows_list
        
        # Deploy the updated flow
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=current_flows,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Previous rides dashboard deployed!")
            return True
        else:
            print(f"❌ Failed to deploy: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Deploy previous rides dashboard"""
    print("📜 Deploying Previous Rides Dashboard")
    print("=" * 50)
    
    if deploy_previous_rides_dashboard():
        print("\n🎉 PREVIOUS RIDES DASHBOARD DEPLOYED!")
        print(f"📱 Dashboard: {NODE_RED_URL}/ui")
        
        print("\n✅ NEW FEATURES:")
        print("   • 📜 Previous Rides section in main dashboard")
        print("   • 🗺️ Map visualization of past rides")
        print("   • 📊 Ride statistics (distance, speed, time)")
        print("   • 🔍 Select any past ride to view details")
        
        print("\n📱 ACCESS YOUR DASHBOARD:")
        print(f"   • Main dashboard: {NODE_RED_URL}/ui")
        print("   • Look for the '📜 Previous Rides' section!")
        print("   • Click 'View Previous Rides' to see detailed history")
        return True
    else:
        return False

if __name__ == "__main__":
    main() 