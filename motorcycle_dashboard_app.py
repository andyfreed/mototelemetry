#!/usr/bin/env python3
"""
Motorcycle Dashboard Web Application
Replaces Node-RED with a clean, remote-accessible dashboard
"""

from flask import Flask, render_template, jsonify, request, Response
from flask_socketio import SocketIO, emit
import sqlite3
import json
import math
import threading
import time
from datetime import datetime, timedelta
import subprocess
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'motorcycle_dashboard_2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
DATABASE_PATH = '/home/pi/motorcycle_data/telemetry.db'
UPDATE_INTERVAL = 2  # seconds

class TelemetryData:
    def __init__(self):
        self.latest_data = {}
        self.gps_status = {}
        self.system_status = {}
        
    def get_latest_telemetry(self):
        """Get latest telemetry data from database"""
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Get latest telemetry record
            cursor.execute('''
                SELECT ax, ay, az, 
                       COALESCE(latitude, 0) as latitude, 
                       COALESCE(longitude, 0) as longitude, 
                       COALESCE(speed_mph, 0) as speed_mph, 
                       COALESCE(gps_fix, 0) as gps_fix, 
                       timestamp 
                FROM telemetry_data 
                ORDER BY timestamp DESC LIMIT 1
            ''')
            
            row = cursor.fetchone()
            if row:
                ax, ay, az, lat, lon, speed, gps_fix, timestamp = row
                
                # Calculate G-forces and lean angle
                X_OFFSET, Y_OFFSET, Z_OFFSET = 0, 0, 0
                SCALE = 16384
                
                forward_g = (ax - X_OFFSET) / SCALE
                lateral_g = (ay - Y_OFFSET) / SCALE
                vertical_g = (az - Z_OFFSET) / SCALE
                
                # Calculate lean angle in degrees
                lean_angle = math.asin(max(-1, min(1, lateral_g))) * 57.3
                
                # GPS status
                has_valid_coords = (lat != 0 and lon != 0)
                has_gps_fix = bool(gps_fix)
                has_valid_gps = has_valid_coords and has_gps_fix
                
                # Data age - handle UTC timestamps properly
                try:
                    from datetime import timezone
                    if timestamp.endswith('+00:00'):
                        data_time = datetime.fromisoformat(timestamp)
                        # Convert to local time for comparison
                        data_age = (datetime.now(timezone.utc) - data_time).total_seconds()
                    else:
                        # Handle timestamps without timezone info
                        data_time = datetime.fromisoformat(timestamp)
                        data_age = (datetime.now() - data_time).total_seconds()
                except:
                    data_age = 0
                
                self.latest_data = {
                    'lean_angle': round(lean_angle, 1),
                    'forward_g': round(forward_g, 3),
                    'lateral_g': round(lateral_g, 3),
                    'vertical_g': round(vertical_g, 3),
                    'speed': round(speed, 1),
                    'latitude': lat,
                    'longitude': lon,
                    'gps_fix': gps_fix,
                    'timestamp': timestamp,
                    'data_age': round(data_age, 1)
                }
                
                self.gps_status = {
                    'has_gps': has_valid_gps,
                    'has_gps_fix': has_gps_fix,
                    'has_valid_coords': has_valid_coords,
                    'status_text': 'GPS Lock Acquired' if has_valid_gps else 
                                  ('GPS Fix but Invalid Coordinates' if has_gps_fix else 'No GPS Data - Check Hardware'),
                    'last_update': data_time.strftime('%H:%M:%S') if 'data_time' in locals() else 'Unknown',
                    'data_age': round(data_age, 1)
                }
            
            # Get record count for last 5 minutes
            cursor.execute('''
                SELECT COUNT(*) FROM telemetry_data 
                WHERE timestamp > datetime("now", "-5 minutes")
            ''')
            recent_count = cursor.fetchone()[0]
            
            # Get total record count
            cursor.execute('SELECT COUNT(*) FROM telemetry_data')
            total_count = cursor.fetchone()[0]
            
            self.system_status = {
                'recent_records': recent_count,
                'total_records': total_count,
                'data_rate': round(recent_count / 5, 1) if recent_count > 0 else 0,
                'status': 'Active' if data_age < 10 else ('Delayed' if data_age < 30 else 'Stalled'),
                'last_update': self.latest_data.get('timestamp', 'Unknown')
            }
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def get_service_status(self):
        """Get system service status"""
        services = [
            'motorcycle-telemetry',
            'gpsd',
            'gps-proxy',
            'route-tracker',
            'tailscaled'
        ]
        
        status = {}
        for service in services:
            try:
                result = subprocess.run(['systemctl', 'is-active', service], 
                                      capture_output=True, text=True)
                status[service] = result.stdout.strip() == 'active'
            except:
                status[service] = False
        
        return status

# Global telemetry data instance
telemetry = TelemetryData()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/telemetry')
def api_telemetry():
    """API endpoint for current telemetry data"""
    telemetry.get_latest_telemetry()
    return jsonify({
        'telemetry': telemetry.latest_data,
        'gps_status': telemetry.gps_status,
        'system_status': telemetry.system_status,
        'services': telemetry.get_service_status(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/gps_history')
def api_gps_history():
    """API endpoint for GPS track history"""
    try:
        hours = request.args.get('hours', 1, type=int)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT latitude, longitude, speed_mph, timestamp 
            FROM telemetry_data 
            WHERE latitude != 0 AND longitude != 0 
            AND timestamp > datetime("now", "-{} hours")
            ORDER BY timestamp DESC
            LIMIT 1000
        '''.format(hours))
        
        points = []
        for row in cursor.fetchall():
            lat, lon, speed, timestamp = row
            points.append({
                'lat': lat,
                'lon': lon,
                'speed': speed,
                'timestamp': timestamp
            })
        
        conn.close()
        return jsonify({'points': points})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/camera/stream.mjpg')
def camera_stream():
    """Proxy camera stream from camera service"""
    try:
        def generate():
            response = requests.get('http://localhost:8090/stream.mjpg', stream=True)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        
        return Response(generate(), 
                       mimetype='multipart/x-mixed-replace; boundary=FRAME')
    except Exception as e:
        print(f"Camera stream error: {e}")
        return Response("Camera not available", status=503)

@app.route('/camera/snapshot')
def camera_snapshot():
    """Proxy camera snapshot from camera service"""
    try:
        response = requests.get('http://localhost:8090/snapshot')
        return Response(response.content, 
                       status=response.status_code,
                       headers={'Content-Type': 'application/json'})
    except Exception as e:
        print(f"Camera snapshot error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('status', {'msg': 'Connected to motorcycle dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

def background_updates():
    """Background thread for real-time updates"""
    while True:
        if telemetry.get_latest_telemetry():
            socketio.emit('telemetry_update', {
                'telemetry': telemetry.latest_data,
                'gps_status': telemetry.gps_status,
                'system_status': telemetry.system_status
            })
        time.sleep(UPDATE_INTERVAL)

# Start background updates
def start_background_updates():
    update_thread = threading.Thread(target=background_updates)
    update_thread.daemon = True
    update_thread.start()

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🏍️ Starting Motorcycle Dashboard...")
    print("📊 Dashboard: http://0.0.0.0:3000")
    print("🌐 Remote access: http://100.119.155.66:3000")
    
    start_background_updates()
    socketio.run(app, host='0.0.0.0', port=3000, debug=False, allow_unsafe_werkzeug=True, log_output=True) 