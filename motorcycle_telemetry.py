#!/usr/bin/env python3
"""
Motorcycle Telemetry System
Records IMU and GPS data during rides, auto-detects engine on/off
"""

import qwiic_icm20948
try:
    import gps
except ImportError:
    # Try alternative GPS library
    import gpsd as gps
import json
import time
import threading
import sqlite3
import os
import sys
import signal
from datetime import datetime, timezone
import requests
import subprocess
import logging
from pathlib import Path
from influxdb import InfluxDBClient

# Configuration
DATA_DIR = Path("/home/pi/motorcycle_data")
DB_PATH = DATA_DIR / "telemetry.db"
LOG_PATH = DATA_DIR / "telemetry.log"
HOME_WIFI_SSID = "Ncwf1"  # Your home WiFi network
UPLOAD_URL = "http://your-server.com/api/telemetry"  # Configure your server

# Engine detection parameters
SAMPLE_RATE = 10           # Hz - samples per second

# Power monitoring (for UPS hat with external power detection)
POWER_CHECK_INTERVAL = 5   # Check power status every 5 seconds
UPS_HAT_PRESENT = False    # Set to False if no UPS hat installed (TESTING MODE)

# InfluxDB configuration for real-time data
INFLUXDB_HOST = 'localhost'
INFLUXDB_PORT = 8086
INFLUXDB_DATABASE = 'motorcycle_telemetry'

class MotorcycleTelemetry:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.setup_database()
        
        # Initialize sensors
        self.imu = None
        self.gps_session = None
        
        # Initialize InfluxDB client for real-time data
        self.influx_client = None
        
        # State tracking
        self.engine_running = False
        self.ride_session_id = None
        self.running = True
        
        # Power monitoring
        self.external_power = False
        self.last_power_check = 0
        
        # Threading
        self.data_lock = threading.Lock()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def setup_logging(self):
        """Setup logging configuration"""
        DATA_DIR.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_PATH),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_directories(self):
        """Create necessary directories"""
        DATA_DIR.mkdir(exist_ok=True)
        
    def setup_database(self):
        """Initialize SQLite database for local data storage"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                uploaded BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TIMESTAMP,
                ax REAL, ay REAL, az REAL,
                gx REAL, gy REAL, gz REAL,
                mx REAL, my REAL, mz REAL,
                temperature REAL,
                vibration_level REAL,
                power_voltage REAL,
                on_external_power BOOLEAN,
                latitude REAL,
                longitude REAL,
                speed_mph REAL,
                heading REAL,
                gps_fix BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES rides (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def initialize_sensors(self):
        """Initialize IMU and GPS sensors"""
        # Initialize IMU
        try:
            self.imu = qwiic_icm20948.QwiicIcm20948()
            if not self.imu.connected:
                self.logger.error("IMU not detected. Check wiring!")
                return False
            if not self.imu.begin():
                self.logger.error("Failed to initialize IMU")
                return False
            self.logger.info("✅ IMU initialized successfully")
        except Exception as e:
            self.logger.error(f"IMU initialization error: {e}")
            return False
            
        # Initialize GPS
        try:
            from gps3 import gps3
            self.gps_socket = gps3.GPSDSocket()
            self.gps_socket.connect()
            self.gps_socket.watch()
            self.data_stream = gps3.DataStream()
            self.logger.info("✅ GPS initialized successfully")
        except Exception as e:
            self.logger.error(f"GPS initialization error: {e}")
            # Continue without GPS - some rides might be indoors
            self.gps_socket = None
            self.data_stream = None
            
        # Initialize InfluxDB client
        try:
            self.influx_client = InfluxDBClient(
                host=INFLUXDB_HOST, 
                port=INFLUXDB_PORT, 
                database=INFLUXDB_DATABASE
            )
            # Ensure database exists
            self.influx_client.create_database(INFLUXDB_DATABASE)
            self.logger.info("✅ InfluxDB connected for real-time data")
        except Exception as e:
            self.logger.warning(f"InfluxDB connection failed: {e} - continuing with SQLite only")
            self.influx_client = None
            
        return True
        
    def get_current_wifi_ssid(self):
        """Get currently connected WiFi SSID"""
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
            
    def is_at_home(self):
        """Check if we're connected to home WiFi"""
        current_ssid = self.get_current_wifi_ssid()
        return current_ssid == HOME_WIFI_SSID
        
    def check_external_power(self):
        """Check if external power is connected (from bike's buck converter)"""
        if not UPS_HAT_PRESENT:
            return True  # Assume always powered if no UPS hat
            
        try:
            # Check for common UPS hat power indicators
            # This varies by UPS hat model - adjust for your specific hat
            
            # Method 1: Check if charging (indicates external power)
            if os.path.exists('/sys/class/power_supply/BAT/status'):
                with open('/sys/class/power_supply/BAT/status', 'r') as f:
                    status = f.read().strip()
                    return status in ['Charging', 'Not charging', 'Full']
            
            # Method 2: Check voltage levels (higher voltage = external power)
            if os.path.exists('/sys/class/power_supply/BAT/voltage_now'):
                with open('/sys/class/power_supply/BAT/voltage_now', 'r') as f:
                    voltage = int(f.read().strip()) / 1000000  # Convert to volts
                    return voltage > 4.0  # External power typically shows higher voltage
                    
            # Method 3: GPIO pin check (if UPS hat has power detection pin)
            # You may need to configure this based on your specific UPS hat
            
            return False  # Default to battery power if unsure
            
        except Exception as e:
            self.logger.warning(f"Could not check power status: {e}")
            return False
            
    def update_power_status(self):
        """Update external power status"""
        current_time = time.time()
        if current_time - self.last_power_check > POWER_CHECK_INTERVAL:
            old_status = self.external_power
            self.external_power = self.check_external_power()
            self.last_power_check = current_time
            
            # Log power state changes
            if old_status != self.external_power:
                if self.external_power:
                    self.logger.info("🔌 External power connected (bike power)")
                else:
                    self.logger.info("🔋 Running on battery power (UPS)")
        
    def detect_engine_state(self, imu_data):
        """Detect if engine is running based on external power only"""
        # Update power status
        self.update_power_status()
        
        # Simple power-based engine detection
        # Engine is running if external power is connected
        return self.external_power
        
    def read_imu_data(self):
        """Read data from IMU sensor"""
        if not self.imu or not self.imu.dataReady():
            return None
            
        try:
            self.imu.getAgmt()  # reads accel, gyro, mag, temp
            return {
                'ax': self.imu.axRaw, 'ay': self.imu.ayRaw, 'az': self.imu.azRaw,
                'gx': self.imu.gxRaw, 'gy': self.imu.gyRaw, 'gz': self.imu.gzRaw,
                'mx': self.imu.mxRaw, 'my': self.imu.myRaw, 'mz': self.imu.mzRaw,
                'temperature': getattr(self.imu, 'tempRaw', None)
            }
        except Exception as e:
            self.logger.error(f"Error reading IMU: {e}")
            return None
            
    def read_gps_data(self):
        """Read data from GPS sensor"""
        if not self.gps_socket or not self.data_stream:
            return None
            
        try:
            new_data = self.gps_socket.next()
            if new_data:
                self.data_stream.unpack(new_data)
                
                # Check if we have valid GPS data
                if hasattr(self.data_stream, 'TPV'):
                    tpv = self.data_stream.TPV
                    # TPV is a dictionary, not an object
                    if 'lat' in tpv and 'lon' in tpv and tpv['lat'] != 'n/a' and tpv['lon'] != 'n/a':
                        speed_ms = tpv.get('speed', None)
                        speed_ms = speed_ms if speed_ms != 'n/a' else None
                        return {
                            'latitude': float(tpv['lat']) if tpv['lat'] != 'n/a' else None,
                            'longitude': float(tpv['lon']) if tpv['lon'] != 'n/a' else None,
                            'speed_mph': float(speed_ms) * 2.237 if speed_ms else None,  # Convert m/s to mph
                            'heading': float(tpv.get('track', 0)) if tpv.get('track', 'n/a') != 'n/a' else None,
                            'gps_fix': tpv.get('mode', 0) >= 2
                        }
        except Exception as e:
            # GPS might not have fix yet
            pass
            
        return None
        
    def start_ride_session(self):
        """Start a new ride session"""
        self.ride_session_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO rides (session_id, start_time) VALUES (?, ?)',
            (self.ride_session_id, datetime.now(timezone.utc))
        )
        conn.commit()
        conn.close()
        
        self.logger.info(f"🏍️  Started ride session: {self.ride_session_id}")
        
    def end_ride_session(self):
        """End the current ride session"""
        if not self.ride_session_id:
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE rides SET end_time = ? WHERE session_id = ?',
            (datetime.now(timezone.utc), self.ride_session_id)
        )
        conn.commit()
        conn.close()
        
        self.logger.info(f"🛑 Ended ride session: {self.ride_session_id}")
        
        # Try to upload data if at home
        if self.is_at_home():
            self.upload_ride_data(self.ride_session_id)
            
        self.ride_session_id = None
        
    def save_telemetry_data(self, imu_data, gps_data):
        """Save telemetry data to database"""
        if not self.ride_session_id:
            return
            
        timestamp = datetime.now(timezone.utc)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Note: Vibration data collection disabled per user request
        # Still calculate internally for engine detection but don't store
        
        cursor.execute('''
            INSERT INTO telemetry_data 
            (session_id, timestamp, ax, ay, az, gx, gy, gz, mx, my, mz, temperature,
             vibration_level, power_voltage, on_external_power, 
             latitude, longitude, speed_mph, heading, gps_fix)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.ride_session_id, timestamp,
            imu_data.get('ax') if imu_data else None,
            imu_data.get('ay') if imu_data else None,
            imu_data.get('az') if imu_data else None,
            imu_data.get('gx') if imu_data else None,
            imu_data.get('gy') if imu_data else None,
            imu_data.get('gz') if imu_data else None,
            imu_data.get('mx') if imu_data else None,
            imu_data.get('my') if imu_data else None,
            imu_data.get('mz') if imu_data else None,
            imu_data.get('temperature') if imu_data else None,
            None,  # vibration_level - disabled per user request
            0,  # power_voltage (placeholder)
            self.external_power,
            gps_data.get('latitude') if gps_data else None,
            gps_data.get('longitude') if gps_data else None,
            gps_data.get('speed_mph') if gps_data else None,
            gps_data.get('heading') if gps_data else None,
            gps_data.get('gps_fix', False) if gps_data else False,
        ))
        
        conn.commit()
        conn.close()
        
        # Also save to InfluxDB for real-time dashboard updates
        self.save_to_influxdb(imu_data, gps_data, timestamp)
        
    def save_to_influxdb(self, imu_data, gps_data, timestamp):
        """Save telemetry data to InfluxDB for real-time visualization"""
        if not self.influx_client or not self.ride_session_id:
            return
            
        try:
            points = []
            
            # GPS data point
            if gps_data and gps_data.get('latitude') is not None and gps_data.get('gps_fix'):
                gps_point = {
                    "measurement": "gps",
                    "tags": {"session": self.ride_session_id},
                    "time": timestamp,
                    "fields": {
                        "latitude": float(gps_data['latitude']),
                        "longitude": float(gps_data['longitude'])
                    }
                }
                if gps_data.get('speed_mph') is not None:
                    gps_point["fields"]["speed_mph"] = float(gps_data['speed_mph'])
                if gps_data.get('heading') is not None:
                    gps_point["fields"]["heading"] = float(gps_data['heading'])
                points.append(gps_point)
            
            # IMU data points
            if imu_data:
                # Accelerometer
                if imu_data.get('ax') is not None:
                    points.append({
                        "measurement": "imu",
                        "tags": {"session": self.ride_session_id, "sensor": "accelerometer"},
                        "time": timestamp,
                        "fields": {
                            "x": float(imu_data['ax']),
                            "y": float(imu_data['ay']),
                            "z": float(imu_data['az'])
                        }
                    })
                    
                # Gyroscope
                if imu_data.get('gx') is not None:
                    points.append({
                        "measurement": "imu",
                        "tags": {"session": self.ride_session_id, "sensor": "gyroscope"},
                        "time": timestamp,
                        "fields": {
                            "x": float(imu_data['gx']),
                            "y": float(imu_data['gy']),
                            "z": float(imu_data['gz'])
                        }
                    })
                    
                # Magnetometer
                if imu_data.get('mx') is not None:
                    points.append({
                        "measurement": "imu",
                        "tags": {"session": self.ride_session_id, "sensor": "magnetometer"},
                        "time": timestamp,
                        "fields": {
                            "x": float(imu_data['mx']),
                            "y": float(imu_data['my']),
                            "z": float(imu_data['mz'])
                        }
                    })
                    
                # Temperature
                if imu_data.get('temperature') is not None:
                    points.append({
                        "measurement": "temperature",
                        "tags": {"session": self.ride_session_id},
                        "time": timestamp,
                        "fields": {"value": float(imu_data['temperature'])}
                    })
            
            # Power data
            points.append({
                "measurement": "power",
                "tags": {"session": self.ride_session_id},
                "time": timestamp,
                "fields": {
                    "voltage": 0.0,  # placeholder
                    "external_power": bool(self.external_power)
                }
            })
            
            # Write to InfluxDB
            if points:
                self.influx_client.write_points(points)
                
        except Exception as e:
            self.logger.warning(f"Failed to write to InfluxDB: {e}")
        
    def upload_ride_data(self, session_id):
        """Upload ride data to server (when at home)"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get ride data
            cursor.execute(
                'SELECT * FROM telemetry_data WHERE session_id = ?',
                (session_id,)
            )
            data = cursor.fetchall()
            
            if not data:
                return
                
            # Convert to JSON format
            columns = [desc[0] for desc in cursor.description]
            ride_data = [dict(zip(columns, row)) for row in data]
            
            # Upload to server (implement your upload logic here)
            # response = requests.post(UPLOAD_URL, json={'ride_data': ride_data})
            
            # Mark as uploaded
            cursor.execute(
                'UPDATE rides SET uploaded = TRUE WHERE session_id = ?',
                (session_id,)
            )
            conn.commit()
            conn.close()
            
            self.logger.info(f"📤 Uploaded ride data: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to upload ride data: {e}")
            
    def main_loop(self):
        """Main telemetry collection loop"""
        if not self.initialize_sensors():
            self.logger.error("Failed to initialize sensors")
            return
            
        self.logger.info("🏍️  Motorcycle telemetry system started")
        
        while self.running:
            try:
                # Read sensor data
                imu_data = self.read_imu_data()
                gps_data = self.read_gps_data()
                
                # Detect engine state
                engine_currently_running = self.detect_engine_state(imu_data)
                
                # Handle engine state changes
                if engine_currently_running and not self.engine_running:
                    # Engine just started
                    self.engine_running = True
                    self.start_ride_session()
                    
                elif not engine_currently_running and self.engine_running:
                    # Engine just stopped
                    self.engine_running = False
                    self.end_ride_session()
                    
                # Save data if engine is running
                if self.engine_running:
                    self.save_telemetry_data(imu_data, gps_data)
                    
                # Sleep for next sample
                time.sleep(1.0 / SAMPLE_RATE)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(1)
                
        self.cleanup()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Received shutdown signal")
        self.running = False
        
    def cleanup(self):
        """Cleanup resources"""
        if self.engine_running:
            self.end_ride_session()
        self.logger.info("🛑 Motorcycle telemetry system stopped")

if __name__ == "__main__":
    telemetry = MotorcycleTelemetry()
    telemetry.main_loop() 