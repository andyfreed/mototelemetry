#!/usr/bin/env python3
"""
Enhanced Motorcycle Telemetry System with Continuous GPS
Records IMU and GPS data during rides with improved GPS performance
"""

import qwiic_icm20948
from gps3 import gps3
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
from collections import deque

# Configuration
DATA_DIR = Path("/home/pi/motorcycle_data")
DB_PATH = DATA_DIR / "telemetry.db"
LOG_PATH = DATA_DIR / "telemetry.log"
HOME_WIFI_SSID = "Ncwf1"
UPLOAD_URL = "http://your-server.com/api/telemetry"

# Engine detection parameters
SAMPLE_RATE = 10           # Hz - samples per second
GPS_UPDATE_RATE = 1        # Hz - GPS updates per second

# Power monitoring
POWER_CHECK_INTERVAL = 5
UPS_HAT_PRESENT = False

class MotorcycleTelemetry:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.setup_database()
        
        # Initialize sensors
        self.imu = None
        self.gps_socket = None
        self.data_stream = None
        
        # State tracking
        self.engine_running = False
        self.ride_session_id = None
        self.running = True
        
        # Power monitoring
        self.external_power = False
        self.last_power_check = 0
        
        # GPS data cache with thread safety
        self.gps_lock = threading.Lock()
        self.latest_gps_data = None
        self.gps_history = deque(maxlen=10)  # Keep last 10 GPS readings
        self.gps_thread = None
        self.gps_stats = {
            'total_reads': 0,
            'successful_reads': 0,
            'last_fix_time': None,
            'satellites_used': 0
        }
        
        # Threading
        self.data_lock = threading.Lock()
        
        # Setup signal handlers
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
                satellites_used INTEGER,
                hdop REAL,
                FOREIGN KEY (session_id) REFERENCES rides (session_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ride_id TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                speed_mph REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status (
                id INTEGER PRIMARY KEY,
                current_ride_id TEXT,
                tracking_active INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute("INSERT OR IGNORE INTO status (id, tracking_active) VALUES (1, 0)")
        
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
            
        # Initialize GPS with continuous reading thread
        try:
            self.gps_socket = gps3.GPSDSocket()
            self.gps_socket.connect()
            self.gps_socket.watch()
            self.data_stream = gps3.DataStream()
            
            # Start GPS reading thread
            self.gps_thread = threading.Thread(target=self.gps_reader_thread, daemon=True)
            self.gps_thread.start()
            
            self.logger.info("✅ GPS initialized with continuous reading")
        except Exception as e:
            self.logger.error(f"GPS initialization error: {e}")
            self.gps_socket = None
            self.data_stream = None
            
        return True
    
    def gps_reader_thread(self):
        """Continuous GPS reading thread for better performance"""
        self.logger.info("🛰️ GPS reader thread started")
        
        while self.running:
            try:
                new_data = self.gps_socket.next(timeout=0.5)
                if new_data:
                    self.data_stream.unpack(new_data)
                    
                    # Process TPV (Time-Position-Velocity) data
                    if hasattr(self.data_stream, 'TPV'):
                        tpv = self.data_stream.TPV
                        if isinstance(tpv, dict) and 'lat' in tpv and 'lon' in tpv:
                            if tpv['lat'] != 'n/a' and tpv['lon'] != 'n/a':
                                # Valid GPS data
                                gps_data = {
                                    'latitude': float(tpv['lat']),
                                    'longitude': float(tpv['lon']),
                                    'speed_mph': float(tpv.get('speed', 0)) * 2.237 if tpv.get('speed', 'n/a') != 'n/a' else 0,
                                    'heading': float(tpv.get('track', 0)) if tpv.get('track', 'n/a') != 'n/a' else None,
                                    'gps_fix': tpv.get('mode', 0) >= 2,
                                    'hdop': float(tpv.get('hdop', 99)) if tpv.get('hdop', 'n/a') != 'n/a' else 99,
                                    'timestamp': datetime.now(timezone.utc)
                                }
                                
                                # Update latest GPS data with thread safety
                                with self.gps_lock:
                                    self.latest_gps_data = gps_data
                                    self.gps_history.append(gps_data)
                                    self.gps_stats['successful_reads'] += 1
                                    self.gps_stats['last_fix_time'] = datetime.now(timezone.utc)
                    
                    # Process SKY data for satellite info
                    if hasattr(self.data_stream, 'SKY'):
                        sky = self.data_stream.SKY
                        if isinstance(sky, dict) and 'uSat' in sky:
                            with self.gps_lock:
                                self.gps_stats['satellites_used'] = int(sky.get('uSat', 0))
                    
                    with self.gps_lock:
                        self.gps_stats['total_reads'] += 1
                        
            except Exception as e:
                if self.running:  # Only log if we're still supposed to be running
                    self.logger.warning(f"GPS reader thread error: {e}")
                time.sleep(0.1)
        
        self.logger.info("🛑 GPS reader thread stopped")
        
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
        """Check if external power is connected"""
        if not UPS_HAT_PRESENT:
            return True
            
        try:
            if os.path.exists('/sys/class/power_supply/BAT/status'):
                with open('/sys/class/power_supply/BAT/status', 'r') as f:
                    status = f.read().strip()
                    return status in ['Charging', 'Not charging', 'Full']
            
            if os.path.exists('/sys/class/power_supply/BAT/voltage_now'):
                with open('/sys/class/power_supply/BAT/voltage_now', 'r') as f:
                    voltage = int(f.read().strip()) / 1000000
                    return voltage > 4.0
                    
            return False
            
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
            
            if old_status != self.external_power:
                if self.external_power:
                    self.logger.info("🔌 External power connected (bike power)")
                else:
                    self.logger.info("🔋 Running on battery power (UPS)")
        
    def detect_engine_state(self, imu_data):
        """Detect if engine is running based on external power"""
        self.update_power_status()
        return self.external_power
        
    def read_imu_data(self):
        """Read data from IMU sensor"""
        if not self.imu or not self.imu.dataReady():
            return None
            
        try:
            self.imu.getAgmt()
            return {
                'ax': self.imu.axRaw, 'ay': self.imu.ayRaw, 'az': self.imu.azRaw,
                'gx': self.imu.gxRaw, 'gy': self.imu.gyRaw, 'gz': self.imu.gzRaw,
                'mx': self.imu.mxRaw, 'my': self.imu.myRaw, 'mz': self.imu.mzRaw,
                'temperature': getattr(self.imu, 'tempRaw', None)
            }
        except Exception as e:
            self.logger.error(f"Error reading IMU: {e}")
            return None
            
    def get_latest_gps_data(self):
        """Get the latest GPS data from the continuous reader"""
        with self.gps_lock:
            if self.latest_gps_data:
                # Return a copy to avoid thread safety issues
                return self.latest_gps_data.copy()
            return None
        
    def get_gps_stats(self):
        """Get GPS performance statistics"""
        with self.gps_lock:
            stats = self.gps_stats.copy()
            if stats['total_reads'] > 0:
                stats['success_rate'] = (stats['successful_reads'] / stats['total_reads']) * 100
            else:
                stats['success_rate'] = 0
            return stats
        
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
        
        # Log GPS stats at ride start
        stats = self.get_gps_stats()
        self.logger.info(f"🏍️ Started ride session: {self.ride_session_id}")
        self.logger.info(f"📡 GPS Stats: {stats['satellites_used']} satellites, {stats['success_rate']:.1f}% success rate")
        
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
        
        # Log final GPS stats
        stats = self.get_gps_stats()
        self.logger.info(f"🛑 Ended ride session: {self.ride_session_id}")
        self.logger.info(f"📊 Final GPS Stats: {stats['successful_reads']} successful reads, {stats['success_rate']:.1f}% success rate")
        
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
        
        # Get current satellite count
        stats = self.get_gps_stats()
        
        cursor.execute('''
            INSERT INTO telemetry_data 
            (session_id, timestamp, ax, ay, az, gx, gy, gz, mx, my, mz, temperature,
             vibration_level, power_voltage, on_external_power, 
             latitude, longitude, speed_mph, heading, gps_fix, satellites_used, hdop)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            None,  # vibration_level
            0,  # power_voltage
            self.external_power,
            gps_data.get('latitude') if gps_data else None,
            gps_data.get('longitude') if gps_data else None,
            gps_data.get('speed_mph') if gps_data else None,
            gps_data.get('heading') if gps_data else None,
            gps_data.get('gps_fix', False) if gps_data else False,
            stats['satellites_used'],
            gps_data.get('hdop', 99) if gps_data else 99,
        ))
        
        conn.commit()
        conn.close()
        
    def upload_ride_data(self, session_id):
        """Upload ride data to server"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM telemetry_data WHERE session_id = ?',
                (session_id,)
            )
            data = cursor.fetchall()
            
            if not data:
                return
                
            columns = [desc[0] for desc in cursor.description]
            ride_data = [dict(zip(columns, row)) for row in data]
            
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
            
        self.logger.info("🏍️ Enhanced Motorcycle telemetry system started")
        self.logger.info("🛰️ GPS running in continuous mode for better performance")
        
        # Wait for initial GPS fix
        self.logger.info("⏳ Waiting for GPS fix...")
        for i in range(30):  # Wait up to 30 seconds
            if self.get_latest_gps_data():
                stats = self.get_gps_stats()
                self.logger.info(f"✅ GPS ready! {stats['satellites_used']} satellites")
                break
            time.sleep(1)
        
        while self.running:
            try:
                # Read sensor data
                imu_data = self.read_imu_data()
                gps_data = self.get_latest_gps_data()  # Get from continuous reader
                
                # Detect engine state
                engine_currently_running = self.detect_engine_state(imu_data)
                
                # Handle engine state changes
                if engine_currently_running and not self.engine_running:
                    self.engine_running = True
                    self.start_ride_session()
                    
                elif not engine_currently_running and self.engine_running:
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
        self.running = False
        if self.gps_thread:
            self.gps_thread.join(timeout=2)
        if self.engine_running:
            self.end_ride_session()
        self.logger.info("🛑 Enhanced Motorcycle telemetry system stopped")

if __name__ == "__main__":
    telemetry = MotorcycleTelemetry()
    telemetry.main_loop() 