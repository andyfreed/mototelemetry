#!/usr/bin/env python3
"""
Deploy improved dashboard with working GPS map
"""

import requests
import json

NODE_RED_URL = "http://localhost:1880"

# Improved flow with better GPS map handling
flow_config = [
    {
        "id": "motorcycle-dashboard",
        "type": "tab",
        "label": "🏍️ Motorcycle Dashboard",
        "disabled": False,
        "info": "Improved motorcycle dashboard with working GPS map"
    },
    {
        "id": "inject-timer",
        "type": "inject",
        "z": "motorcycle-dashboard",
        "name": "Every 2 seconds",
        "props": [{"p": "payload"}],
        "repeat": "2",
        "crontab": "",
        "once": True,
        "onceDelay": 0.1,
        "topic": "",
        "payload": "",
        "payloadType": "date",
        "x": 140,
        "y": 100,
        "wires": [["get-latest-data"]]
    },
    {
        "id": "get-latest-data",
        "type": "exec",
        "z": "motorcycle-dashboard",
        "command": "sqlite3 /home/pi/motorcycle_data/telemetry.db \"SELECT ax, ay, az, COALESCE(latitude, 0) as latitude, COALESCE(longitude, 0) as longitude, COALESCE(speed_mph, 0) as speed_mph FROM telemetry_data ORDER BY timestamp DESC LIMIT 1\" -json",
        "addpay": "",
        "append": "",
        "useSpawn": "false",
        "timer": "",
        "oldrc": False,
        "name": "Query SQLite",
        "x": 350,
        "y": 100,
        "wires": [["process-data"], [], []]
    },
    {
        "id": "process-data",
        "type": "function",
        "z": "motorcycle-dashboard",
        "name": "Calculate G-Forces & Lean",
        "func": """
if (msg.payload && msg.payload.trim()) {
    try {
        const jsonData = JSON.parse(msg.payload.trim());
        if (jsonData && jsonData.length > 0) {
            const data = jsonData[0];
            
            // Calibration constants
            const X_OFFSET = 6200;
            const Y_OFFSET = 100;
            const Z_OFFSET = 15400;
            const SCALE = 16384;
            
            // Calculate G-forces
            const forwardG = (data.ax - X_OFFSET) / SCALE;
            const lateralG = (data.ay - Y_OFFSET) / SCALE;
            const leanAngle = Math.asin(Math.max(-1, Math.min(1, lateralG))) * 57.3;
            
            // GPS coordinates
            const hasGPS = data.latitude !== 0 || data.longitude !== 0;
            const lat = hasGPS ? parseFloat(data.latitude) : 42.8096;
            const lon = hasGPS ? parseFloat(data.longitude) : -70.8673;
            
            // Update counter
            const count = context.get('counter') || 0;
            context.set('counter', count + 1);
            
            return [
                { payload: parseFloat(leanAngle.toFixed(1)) },
                { payload: parseFloat(forwardG.toFixed(3)) },
                { payload: parseFloat(lateralG.toFixed(3)) },
                { payload: parseFloat(data.speed_mph || 0) },
                { payload: {
                    lat: lat,
                    lon: lon,
                    name: hasGPS ? '🏍️ Motorcycle' : '📍 GPS Searching...',
                    icon: 'motorcycle',
                    iconColor: hasGPS ? 'blue' : 'red'
                }},
                { payload: hasGPS ? 
                    `✅ GPS Active: ${lat.toFixed(6)}, ${lon.toFixed(6)}` :
                    `🔍 GPS Searching... (showing last known location)`
                },
                { payload: count + 1 }
            ];
        }
    } catch (e) {
        node.warn("Parse error: " + e.message);
    }
}
return null;
        """,
        "outputs": 7,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 530,
        "y": 100,
        "wires": [
            ["lean-gauge"],
            ["forward-g-gauge"], 
            ["lateral-g-gauge"],
            ["speed-gauge"],
            ["worldmap-feed"],
            ["gps-status-display"],
            ["counter-display"]
        ]
    },
    {
        "id": "lean-gauge",
        "type": "ui_gauge",
        "z": "motorcycle-dashboard",
        "name": "Lean Angle",
        "group": "gauges",
        "order": 1,
        "width": 4,
        "height": 4,
        "gtype": "gage",
        "title": "🏍️ Lean Angle",
        "label": "degrees",
        "format": "{{value}}°",
        "min": -60,
        "max": 60,
        "colors": ["#00b500","#e6e600","#ca3838"],
        "seg1": 30,
        "seg2": 45,
        "x": 750,
        "y": 40,
        "wires": []
    },
    {
        "id": "forward-g-gauge",
        "type": "ui_gauge",
        "z": "motorcycle-dashboard",
        "name": "Forward G-Force",
        "group": "gauges",
        "order": 2,
        "width": 4,
        "height": 4,
        "gtype": "gage",
        "title": "⚡ Forward G",
        "label": "G",
        "format": "{{value}}g",
        "min": -1.5,
        "max": 1.5,
        "colors": ["#ca3838","#e6e600","#00b500"],
        "seg1": 0.5,
        "seg2": 1.0,
        "x": 750,
        "y": 80,
        "wires": []
    },
    {
        "id": "lateral-g-gauge",
        "type": "ui_gauge",
        "z": "motorcycle-dashboard",
        "name": "Lateral G-Force",
        "group": "gauges",
        "order": 3,
        "width": 4,
        "height": 4,
        "gtype": "gage",
        "title": "🌀 Lateral G",
        "label": "G",
        "format": "{{value}}g",
        "min": -1.2,
        "max": 1.2,
        "colors": ["#ca3838","#e6e600","#00b500"],
        "seg1": 0.4,
        "seg2": 0.8,
        "x": 750,
        "y": 120,
        "wires": []
    },
    {
        "id": "speed-gauge",
        "type": "ui_gauge",
        "z": "motorcycle-dashboard",
        "name": "Speed",
        "group": "performance",
        "order": 1,
        "width": 6,
        "height": 4,
        "gtype": "gage",
        "title": "🚀 Speed",
        "label": "mph",
        "format": "{{value}} mph",
        "min": 0,
        "max": 120,
        "colors": ["#00b500","#e6e600","#ca3838"],
        "seg1": 45,
        "seg2": 70,
        "x": 750,
        "y": 200,
        "wires": []
    },
    {
        "id": "worldmap-feed",
        "type": "worldmap",
        "z": "motorcycle-dashboard",
        "name": "GPS Location",
        "lat": "42.8096",
        "lon": "-70.8673",
        "zoom": "15",
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
        "overlist": "DR,CO,RA,DN",
        "maplist": "OSM,Esri,Nat,OPR",
        "mapname": "",
        "mapurl": "",
        "mapopt": "",
        "mapwms": False,
        "x": 750,
        "y": 260,
        "wires": []
    },
    {
        "id": "map-access-template",
        "type": "ui_template",
        "z": "motorcycle-dashboard",
        "group": "map-access",
        "name": "GPS Map Access",
        "order": 1,
        "width": 12,
        "height": 6,
        "format": """
<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%); border-radius: 15px; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    <h2 style="margin: 0 0 15px 0; font-size: 24px;">🗺️ GPS Location Map</h2>
    <p style="margin: 5px 0 20px 0; font-size: 16px; opacity: 0.9;">View your motorcycle's real-time location</p>
    
    <a href="/worldmap" target="_blank" style="
        display: inline-block;
        background: #FF6B35;
        color: white;
        padding: 15px 30px;
        text-decoration: none;
        border-radius: 30px;
        font-weight: bold;
        font-size: 18px;
        margin: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
    " onmouseover="this.style.background='#E85A2B'; this.style.transform='translateY(-2px)'" 
       onmouseout="this.style.background='#FF6B35'; this.style.transform='translateY(0)'">
        🚁 Open Interactive Map
    </a>
    
    <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 10px;">
        <p style="margin: 5px 0; font-size: 14px;">
            📍 <strong>Current Location:</strong> Massachusetts<br>
            🔄 <strong>Updates:</strong> Every 2 seconds<br>
            🛰️ <strong>GPS Status:</strong> <span id="gps-status">Active</span>
        </p>
    </div>
    
    <p style="margin: 15px 0 0 0; font-size: 12px; opacity: 0.7;">
        💡 Tip: The map opens in a new tab with full functionality
    </p>
</div>
        """,
        "storeOutMessages": False,
        "fwdInMessages": False,
        "resendOnRefresh": True,
        "templateScope": "local",
        "className": "",
        "x": 750,
        "y": 300,
        "wires": [[]]
    },
    {
        "id": "gps-status-display",
        "type": "ui_text",
        "z": "motorcycle-dashboard",
        "group": "gps-info",
        "order": 1,
        "width": 12,
        "height": 2,
        "name": "GPS Status",
        "label": "🛰️ GPS Status",
        "format": "{{msg.payload}}",
        "layout": "row-spread",
        "className": "",
        "x": 750,
        "y": 340,
        "wires": []
    },
    {
        "id": "counter-display",
        "type": "ui_text",
        "z": "motorcycle-dashboard",
        "group": "status",
        "order": 1,
        "width": 12,
        "height": 2,
        "name": "System Status",
        "label": "🛠️ System Status",
        "format": "✅ Node-RED Active | 📊 Data Updates: {{msg.payload}}",
        "layout": "row-spread",
        "className": "",
        "x": 750,
        "y": 380,
        "wires": []
    },
    {
        "id": "gauges",
        "type": "ui_group",
        "name": "G-Force & Lean",
        "tab": "dashboard-tab",
        "order": 1,
        "disp": True,
        "width": "12",
        "collapse": False
    },
    {
        "id": "performance",
        "type": "ui_group",
        "name": "Performance",
        "tab": "dashboard-tab",
        "order": 2,
        "disp": True,
        "width": "12",
        "collapse": False
    },
    {
        "id": "map-access",
        "type": "ui_group",
        "name": "🗺️ GPS Map Access",
        "tab": "dashboard-tab",
        "order": 3,
        "disp": True,
        "width": "12",
        "collapse": False
    },
    {
        "id": "gps-info",
        "type": "ui_group",
        "name": "GPS Information",
        "tab": "dashboard-tab",
        "order": 4,
        "disp": True,
        "width": "12",
        "collapse": False
    },
    {
        "id": "status",
        "type": "ui_group",
        "name": "System Status",
        "tab": "dashboard-tab",
        "order": 5,
        "disp": True,
        "width": "12",
        "collapse": False
    },
    {
        "id": "dashboard-tab",
        "type": "ui_tab",
        "name": "🏍️ Motorcycle Dashboard",
        "icon": "dashboard",
        "order": 1,
        "disabled": False,
        "hidden": False
    }
]

def deploy_improved_dashboard():
    """Deploy the improved dashboard"""
    try:
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=flow_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Improved dashboard deployed successfully!")
            return True
        else:
            print(f"❌ Failed to deploy: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Deploy improved dashboard"""
    print("🚀 Deploying Improved Motorcycle Dashboard")
    print("=" * 50)
    
    if deploy_improved_dashboard():
        print("\n🎉 IMPROVED DASHBOARD DEPLOYED!")
        print(f"📱 Dashboard: {NODE_RED_URL}/ui")
        print(f"🗺️  GPS Map: {NODE_RED_URL}/worldmap")
        
        print("\n✅ WHAT'S FIXED:")
        print("   • Removed gray embedded map widget")
        print("   • Added prominent GPS Map Access button")
        print("   • Map opens in new tab with full functionality")
        print("   • Better GPS status display")
        print("   • Improved styling and layout")
        
        print(f"\n🗺️ GPS MAP ACCESS:")
        print(f"   • Dashboard: {NODE_RED_URL}/ui")
        print(f"   • Click the orange 'Open Interactive Map' button")
        print(f"   • Or go directly: {NODE_RED_URL}/worldmap")
        
        return True
    else:
        return False

if __name__ == "__main__":
    main() 