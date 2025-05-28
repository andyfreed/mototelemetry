#!/usr/bin/env python3
"""
Cellular Web Dashboard for Motorcycle Telemetry
Serves a real-time dashboard accessible over cellular connection
"""

from flask import Flask, render_template_string, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Motorcycle Telemetry Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #fff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .card {
            background: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .metric {
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
            margin: 10px 0;
        }
        .label {
            color: #888;
            font-size: 0.9em;
        }
        #map {
            height: 400px;
            width: 100%;
            border-radius: 10px;
            margin-top: 20px;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.9em;
        }
        .status.connected {
            background: #4CAF50;
        }
        .status.disconnected {
            background: #f44336;
        }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏍️ Motorcycle Telemetry Dashboard</h1>
            <div>
                <span class="status" id="status">Connecting...</span>
                <span id="last-update"></span>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="label">Speed</div>
                <div class="metric" id="speed">0</div>
                <div class="label">mph</div>
            </div>
            
            <div class="card">
                <div class="label">Lean Angle</div>
                <div class="metric" id="lean">0°</div>
                <div class="label">degrees</div>
            </div>
            
            <div class="card">
                <div class="label">G-Force</div>
                <div class="metric" id="gforce">0.0g</div>
                <div class="label">lateral</div>
            </div>
            
            <div class="card">
                <div class="label">GPS Status</div>
                <div class="metric" id="gps-status">No Fix</div>
                <div class="label"><span id="satellites">0</span> satellites</div>
            </div>
        </div>
        
        <div id="map"></div>
    </div>
    
    <script>
        // Initialize map
        var map = L.map('map').setView([42.809586, -70.867404], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        var marker = null;
        var pathCoords = [];
        var path = null;
        
        // Update dashboard
        function updateDashboard() {
            fetch('/api/telemetry')
                .then(response => response.json())
                .then(data => {
                    // Update status
                    document.getElementById('status').textContent = 'Connected';
                    document.getElementById('status').className = 'status connected';
                    document.getElementById('last-update').textContent = 
                        'Last update: ' + new Date().toLocaleTimeString();
                    
                    // Update metrics
                    document.getElementById('speed').textContent = 
                        data.speed ? data.speed.toFixed(1) : '0';
                    document.getElementById('lean').textContent = 
                        data.lean_angle ? data.lean_angle.toFixed(0) + '°' : '0°';
                    document.getElementById('gforce').textContent = 
                        data.gforce_lateral ? data.gforce_lateral.toFixed(2) + 'g' : '0.0g';
                    
                    // Update GPS status
                    if (data.gps_fix) {
                        document.getElementById('gps-status').textContent = 'Fixed';
                        document.getElementById('satellites').textContent = 
                            data.satellites || '0';
                        
                        // Update map
                        if (data.latitude && data.longitude) {
                            var latlng = [data.latitude, data.longitude];
                            
                            if (!marker) {
                                marker = L.marker(latlng).addTo(map);
                            } else {
                                marker.setLatLng(latlng);
                            }
                            
                            // Add to path
                            pathCoords.push(latlng);
                            if (pathCoords.length > 1000) {
                                pathCoords.shift(); // Keep last 1000 points
                            }
                            
                            if (path) {
                                path.setLatLngs(pathCoords);
                            } else {
                                path = L.polyline(pathCoords, {
                                    color: 'red',
                                    weight: 3
                                }).addTo(map);
                            }
                            
                            // Center map on current position
                            map.setView(latlng);
                        }
                    } else {
                        document.getElementById('gps-status').textContent = 'No Fix';
                    }
                })
                .catch(error => {
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').className = 'status disconnected';
                });
        }
        
        // Update every second
        setInterval(updateDashboard, 1000);
        updateDashboard();
    </script>
</body>
</html>
'''

class TelemetryServer:
    def __init__(self, db_path='/home/pi/motorcycle_data/telemetry.db'):
        self.db_path = db_path
        self.latest_data = {}
        self.running = False
        
    def get_latest_telemetry(self):
        """Get the latest telemetry data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get latest record
            cursor.execute("""
                SELECT * FROM telemetry_data 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                data = dict(row)
                
                # Calculate derived values
                if data.get('ax') and data.get('ay'):
                    # Calculate lean angle from accelerometer
                    ax = (data['ax'] - 100) / 16384.0  # Calibrated values
                    ay = (data['ay'] - 100) / 16384.0
                    
                    import math
                    lean_angle = math.atan2(ay, abs(ax)) * 57.3
                    data['lean_angle'] = lean_angle
                    data['gforce_lateral'] = ay
                
                return data
            
            conn.close()
            
        except Exception as e:
            print(f"Database error: {e}")
            
        return {}
    
    def update_loop(self):
        """Continuously update latest data"""
        while self.running:
            self.latest_data = self.get_latest_telemetry()
            time.sleep(0.5)
    
    def start(self):
        """Start the update thread"""
        self.running = True
        update_thread = threading.Thread(target=self.update_loop)
        update_thread.daemon = True
        update_thread.start()
    
    def stop(self):
        """Stop the update thread"""
        self.running = False

# Create server instance
telemetry_server = TelemetryServer()

@app.route('/')
def dashboard():
    """Serve the dashboard HTML"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/telemetry')
def get_telemetry():
    """API endpoint for latest telemetry data"""
    return jsonify(telemetry_server.latest_data)

@app.route('/api/history/<int:minutes>')
def get_history(minutes):
    """Get telemetry history for the last N minutes"""
    try:
        conn = sqlite3.connect(telemetry_server.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calculate time threshold
        threshold = datetime.now() - timedelta(minutes=minutes)
        
        cursor.execute("""
            SELECT timestamp, latitude, longitude, speed_mph, ax, ay 
            FROM telemetry_data 
            WHERE timestamp > ? 
            AND latitude IS NOT NULL 
            ORDER BY timestamp DESC 
            LIMIT 1000
        """, (threshold.isoformat(),))
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        conn.close()
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Cellular Web Dashboard")
    print("==================================")
    
    # Start telemetry updater
    telemetry_server.start()
    
    # Get network interfaces
    import subprocess
    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
    ips = result.stdout.strip().split()
    
    print("\n📡 Dashboard will be accessible at:")
    for ip in ips:
        print(f"   http://{ip}:8080")
    
    print("\n⚠️  Make sure port 8080 is accessible through your cellular connection")
    print("   You may need to configure port forwarding or use a VPN")
    
    try:
        # Run Flask app
        app.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        telemetry_server.stop()
        print("\n🛑 Dashboard stopped") 