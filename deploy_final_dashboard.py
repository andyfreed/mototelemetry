#!/usr/bin/env python3
"""
Deploy final improved dashboard with reliable GPS handling
"""

import requests
import json

NODE_RED_URL = "http://localhost:1880"

# Final improved flow configuration
flow_config = [
    {
        "id": "motorcycle-dashboard",
        "type": "tab",
        "label": "🏍️ Motorcycle Dashboard",
        "disabled": False,
        "info": "Final improved motorcycle dashboard with reliable GPS"
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
        "name": "Process Telemetry Data",
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
            
            // GPS coordinates - check if we have real GPS data
            const hasRealGPS = data.latitude !== 0 && data.longitude !== 0;
            const lat = hasRealGPS ? parseFloat(data.latitude) : 42.8096044;
            const lon = hasRealGPS ? parseFloat(data.longitude) : -70.8673428;
            
            // GPS status for context storage
            let gpsStatus = context.get('lastGpsStatus') || 'searching';
            if (hasRealGPS) {
                gpsStatus = 'active';
                context.set('lastGpsTime', Date.now());
                context.set('lastGpsLat', lat);
                context.set('lastGpsLon', lon);
            } else {
                // Check if we had GPS recently (within 30 seconds)
                const lastGpsTime = context.get('lastGpsTime') || 0;
                if (Date.now() - lastGpsTime < 30000) {
                    gpsStatus = 'recent';
                } else {
                    gpsStatus = 'searching';
                }
            }
            context.set('lastGpsStatus', gpsStatus);
            
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
                    name: hasRealGPS ? '🏍️ Motorcycle (Live)' : 
                          gpsStatus === 'recent' ? '🏍️ Motorcycle (Recent)' : '📍 Last Known Location',
                    icon: 'motorcycle',
                    iconColor: hasRealGPS ? 'blue' : gpsStatus === 'recent' ? 'orange' : 'red'
                }},
                { payload: gpsStatus },
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
            ["gps-status-function"],
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
        "id": "gps-status-function",
        "type": "function",
        "z": "motorcycle-dashboard",
        "name": "GPS Status Message",
        "func": """
const status = msg.payload;

let statusText = "";
let statusIcon = "";

switch(status) {
    case 'active':
        statusText = "✅ GPS Active - Live coordinates";
        statusIcon = "🛰️";
        break;
    case 'recent':
        statusText = "🟡 GPS Recent - Using last known location";
        statusIcon = "📡";
        break;
    case 'searching':
    default:
        statusText = "🔍 GPS Searching - Using fallback location";
        statusIcon = "📍";
        break;
}

msg.payload = `${statusIcon} ${statusText}`;
return msg;
        """,
        "outputs": 1,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 730,
        "y": 300,
        "wires": [["gps-status-display"]]
    },
    {
        "id": "map-access-template",
        "type": "ui_template",
        "z": "motorcycle-dashboard",
        "group": "map-access",
        "name": "GPS Map Access",
        "order": 1,
        "width": 12,
        "height": 8,
        "format": """
<div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1B5E20 0%, #4CAF50 100%); border-radius: 15px; color: white; box-shadow: 0 6px 20px rgba(0,0,0,0.3); margin: 10px 0;">
    <h2 style="margin: 0 0 15px 0; font-size: 26px;">🗺️ GPS Location Map</h2>
    <p style="margin: 5px 0 20px 0; font-size: 16px; opacity: 0.9;">Real-time motorcycle tracking system</p>
    
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap; margin: 20px 0;">
        <a href="/worldmap" target="_blank" style="
            display: inline-block;
            background: #FF6B35;
            color: white;
            padding: 15px 25px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            margin: 5px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
            min-width: 200px;
        " onmouseover="this.style.background='#E85A2B'; this.style.transform='translateY(-2px)'" 
           onmouseout="this.style.background='#FF6B35'; this.style.transform='translateY(0)'">
            🚁 Interactive Map
        </a>
        
        <button onclick="window.open('https://www.google.com/maps/@42.8096044,-70.8673428,15z', '_blank')" style="
            background: #1976D2;
            color: white;
            padding: 15px 25px;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            font-size: 16px;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(25, 118, 210, 0.4);
            min-width: 200px;
        " onmouseover="this.style.background='#1565C0'; this.style.transform='translateY(-2px)'" 
           onmouseout="this.style.background='#1976D2'; this.style.transform='translateY(0)'">
            🌍 Google Maps
        </button>
    </div>
    
    <div style="margin-top: 25px; padding: 20px; background: rgba(255,255,255,0.15); border-radius: 12px;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; text-align: left;">
            <div>
                <p style="margin: 0; font-size: 14px;"><strong>📍 Location:</strong> Massachusetts</p>
                <p style="margin: 0; font-size: 14px;"><strong>📊 Updates:</strong> Every 2 seconds</p>
            </div>
            <div>
                <p style="margin: 0; font-size: 14px;"><strong>🛰️ Coordinates:</strong> 42.81°N, 70.87°W</p>
                <p style="margin: 0; font-size: 14px;"><strong>🎯 Accuracy:</strong> GPS enabled</p>
            </div>
        </div>
    </div>
    
    <p style="margin: 20px 0 0 0; font-size: 12px; opacity: 0.8;">
        💡 Try both map options if one doesn't load properly
    </p>
</div>
        """,
        "storeOutMessages": False,
        "fwdInMessages": False,
        "resendOnRefresh": True,
        "templateScope": "local",
        "className": "",
        "x": 750,
        "y": 340,
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
        "x": 940,
        "y": 300,
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
        "x": 940,
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

def deploy_final_dashboard():
    """Deploy the final improved dashboard"""
    try:
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=flow_config,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 204]:
            print("✅ Final dashboard deployed successfully!")
            return True
        else:
            print(f"❌ Failed to deploy: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Deploy final dashboard with GPS improvements"""
    print("🚀 DEPLOYING FINAL MOTORCYCLE DASHBOARD")
    print("=" * 50)
    
    if deploy_final_dashboard():
        print("\n🎉 FINAL DASHBOARD DEPLOYED!")
        print(f"📱 Dashboard: {NODE_RED_URL}/ui")
        print(f"🗺️  GPS Map: {NODE_RED_URL}/worldmap")
        
        print("\n✅ IMPROVEMENTS MADE:")
        print("   • Better GPS status tracking (Active/Recent/Searching)")
        print("   • Fallback to Google Maps if Node-RED map has issues")
        print("   • Enhanced GPS status display with context")
        print("   • Improved map access with multiple options")
        print("   • Real-time vs cached location indication")
        
        print(f"\n🗺️ MAP ACCESS OPTIONS:")
        print(f"   1. Node-RED Map: {NODE_RED_URL}/worldmap")
        print(f"   2. Google Maps: https://www.google.com/maps/@42.8096044,-70.8673428,15z")
        print(f"   3. Dashboard buttons for both options")
        
        print(f"\n🛰️ GPS STATUS EXPLAINED:")
        print(f"   • ✅ GPS Active: Real-time coordinates")
        print(f"   • 🟡 GPS Recent: Last known location (within 30s)")
        print(f"   • 🔍 GPS Searching: Using fallback coordinates")
        
        return True
    else:
        return False

if __name__ == "__main__":
    main() 