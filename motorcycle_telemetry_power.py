#!/usr/bin/env python3
"""
Power-Based Motorcycle Telemetry System
Detects engine state by monitoring power source instead of vibration
- Buck converter active = Engine/Key On
- UPS battery active = Engine Off
"""

import qwiic_icm20948
import json
import time
import threading
import sqlite3
import os
import sys
import signal
import subprocess
import serial
from datetime import datetime, timezone
import logging
from pathlib import Path

# Configuration
DATA_DIR = Path("/home/pi/motorcycle_data")
DB_PATH = DATA_DIR / "telemetry.db"
LOG_PATH = DATA_DIR / "telemetry.log"

# Power detection parameters
POWER_CHECK_INTERVAL = 2    # Seconds between power checks
ENGINE_OFF_TIMEOUT = 30     # Seconds on battery before considering engine truly off
SAMPLE_RATE = 5            # Hz - IMU samples per second
MIN_VOLTAGE_THRESHOLD = 11.5  # Minimum voltage for buck converter detection

# GPS configuration
GPS_PORT = "/dev/ttyACM0"
GPS_BAUD = 9600

class PowerBasedTelemetry:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.setup_database()
        
        # Initialize sensors
        self.imu = None
        self.gps = None
        
        # GPS data
        self.gps_data = {
            'latitude': 0.0,
            'longitude': 0.0,
            'speed_mph': 0.0,
            'heading': 0.0,
            'fix': False
        }
        
        # State tracking
        self.engine_running = False
        self.on_external_power = False  # Buck converter vs UPS
        self.ride_session_id = None
        self.last_external_power_time = time.time()
        self.running = True
        
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
            self.gps = serial.Serial(GPS_PORT, GPS_BAUD, timeout=1)
            self.logger.info("✅ GPS initialized successfully")
        except Exception as e:
            self.logger.warning(f"GPS initialization failed: {e} - continuing without GPS")
            self.gps = None
            
        return True
            
    def check_power_source(self):
        """
        Check if running on external power (buck converter) or battery (UPS)
        Returns (on_external_power: bool, voltage: float)
        """
        try:
            # Method 1: Check system voltage via vcgencmd (Pi-specific)
            result = subprocess.run(['vcgencmd', 'get_throttled'], 
                                  capture_output=True, text=True, timeout=5)
            throttled = result.stdout.strip()
            
            # Method 2: Check power supply info
            result = subprocess.run(['vcgencmd', 'measure_volts', 'core'], 
                                  capture_output=True, text=True, timeout=5)
            voltage_str = result.stdout.strip()
            
            # Parse voltage (format: "volt=1.2000V")
            if 'volt=' in voltage_str:
                voltage = float(voltage_str.split('=')[1].replace('V', ''))
            else:
                voltage = 0.0
            
            # Method 3: Check if power is stable/sufficient
            # Throttling status: bit 0 = under-voltage, bit 1 = arm frequency capped
            throttled_int = int(throttled.split('=')[1], 16) if '=' in throttled else 0
            under_voltage = bool(throttled_int & 0x1)
            
            # External power is considered active if:
            # - No under-voltage condition
            # - Core voltage is stable
            external_power = not under_voltage and voltage > 1.0
            
            # Simulate actual voltage for logging (this would come from voltage divider)
            estimated_input_voltage = 12.5 if external_power else 3.7
            
            return external_power, estimated_input_voltage
            
        except Exception as e:
            self.logger.error(f"Error checking power source: {e}")
            return False, 0.0
            
    def detect_engine_state(self):
        """Detect if engine is running based on power source"""
        on_power, voltage = self.check_power_source()
        
        if on_power:
            # On external power (buck converter) - engine likely running
            self.on_external_power = True
            self.last_external_power_time = time.time()
            return True
        else:
            # On battery power (UPS)
            self.on_external_power = False
            
            # Check if we've been on battery for too long
            time_on_battery = time.time() - self.last_external_power_time
            
            # Engine considered off if on battery for more than timeout
            return time_on_battery < ENGINE_OFF_TIMEOUT
    
    def parse_nmea_sentence(self, sentence):
        """Parse NMEA GPS sentence"""
        try:
            if sentence.startswith('$GPRMC'):
                # Recommended Minimum Course - has position, speed, course
                parts = sentence.split(',')
                if len(parts) >= 10 and parts[2] == 'A':  # A = valid fix
                    # Parse latitude
                    lat_raw = parts[3]
                    lat_dir = parts[4]
                    if lat_raw and lat_dir:
                        lat_deg = float(lat_raw[:2])
                        lat_min = float(lat_raw[2:])
                        latitude = lat_deg + (lat_min / 60.0)
                        if lat_dir == 'S':
                            latitude = -latitude
                        self.gps_data['latitude'] = latitude
                    
                    # Parse longitude  
                    lon_raw = parts[5]
                    lon_dir = parts[6]
                    if lon_raw and lon_dir:
                        lon_deg = float(lon_raw[:3])
                        lon_min = float(lon_raw[3:])
                        longitude = lon_deg + (lon_min / 60.0)
                        if lon_dir == 'W':
                            longitude = -longitude
                        self.gps_data['longitude'] = longitude
                    
                    # Parse speed (knots to mph)
                    if parts[7]:
                        speed_knots = float(parts[7])
                        self.gps_data['speed_mph'] = speed_knots * 1.151  # Convert knots to mph
                    
                    # Parse course/heading
                    if parts[8]:
                        self.gps_data['heading'] = float(parts[8])
                    
                    self.gps_data['fix'] = True
                    return True
                    
        except (ValueError, IndexError) as e:
            pass  # Ignore malformed sentences
        return False
    
    def read_gps_data(self):
        """Read and parse GPS data"""
        if not self.gps:
            return
            
        try:
            while self.gps.in_waiting:
                line = self.gps.readline().decode('ascii', errors='ignore').strip()
                if line:
                    self.parse_nmea_sentence(line)
        except Exception as e:
            pass  # Ignore GPS read errors
        
    def read_imu_data(self):
        """Read data from IMU and GPS sensors"""
        if not self.imu or not self.imu.dataReady():
            return None
            
        try:
            # Read GPS data first
            self.read_gps_data()
            
            # Read IMU data
            self.imu.getAgmt()  # reads accel, gyro, mag, temp
            
            # Calculate vibration level for analysis (not engine detection)
            vibration_level = abs(self.imu.axRaw) + abs(self.imu.ayRaw) + abs(self.imu.azRaw)
            
            # Get power info
            on_power, voltage = self.check_power_source()
            
            return {
                'ax': self.imu.axRaw, 'ay': self.imu.ayRaw, 'az': self.imu.azRaw,
                'gx': self.imu.gxRaw, 'gy': self.imu.gyRaw, 'gz': self.imu.gzRaw,
                'mx': self.imu.mxRaw, 'my': self.imu.myRaw, 'mz': self.imu.mzRaw,
                'temperature': getattr(self.imu, 'tempRaw', None),
                'vibration_level': vibration_level,
                'power_voltage': voltage,
                'on_external_power': on_power,
                'latitude': self.gps_data['latitude'],
                'longitude': self.gps_data['longitude'],
                'speed_mph': self.gps_data['speed_mph'],
                'heading': self.gps_data['heading'],
                'gps_fix': self.gps_data['fix']
            }
        except Exception as e:
            self.logger.error(f"Error reading sensors: {e}")
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
        self.ride_session_id = None
        
    def save_telemetry_data(self, sensor_data):
        """Save telemetry data to database"""
        if not self.ride_session_id:
            return
            
        timestamp = datetime.now(timezone.utc)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO telemetry_data 
            (session_id, timestamp, ax, ay, az, gx, gy, gz, mx, my, mz, 
             temperature, vibration_level, power_voltage, on_external_power,
             latitude, longitude, speed_mph, heading, gps_fix)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.ride_session_id, timestamp,
            sensor_data['ax'], sensor_data['ay'], sensor_data['az'],
            sensor_data['gx'], sensor_data['gy'], sensor_data['gz'],
            sensor_data['mx'], sensor_data['my'], sensor_data['mz'],
            sensor_data['temperature'], sensor_data['vibration_level'],
            sensor_data['power_voltage'], sensor_data['on_external_power'],
            sensor_data['latitude'], sensor_data['longitude'], 
            sensor_data['speed_mph'], sensor_data['heading'], sensor_data['gps_fix']
        ))
        
        conn.commit()
        conn.close()
        
    def main_loop(self):
        """Main telemetry collection loop"""
        if not self.initialize_sensors():
            self.logger.error("Failed to initialize sensors")
            return
            
        self.logger.info("🏍️  Power-based telemetry system started")
        self.logger.info("💡 Key on/engine start will trigger recording")
        
        sample_interval = 1.0 / SAMPLE_RATE
        last_sample_time = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Read sensor data
                sensor_data = self.read_imu_data()
                if not sensor_data:
                    time.sleep(0.1)
                    continue
                
                # Detect engine state based on power
                engine_currently_running = self.detect_engine_state()
                
                # Handle engine state transitions
                if engine_currently_running and not self.engine_running:
                    # Engine just started
                    self.engine_running = True
                    self.start_ride_session()
                elif not engine_currently_running and self.engine_running:
                    # Engine just stopped
                    self.engine_running = False
                    self.end_ride_session()
                
                # Log current status
                if self.engine_running:
                    power_status = "🔌 EXTERNAL" if sensor_data['on_external_power'] else "🔋 BATTERY"
                    gps_status = "🛰️ GPS" if sensor_data['gps_fix'] else "❌ No GPS"
                    if sensor_data['gps_fix']:
                        print(f"📊 Recording... Power: {power_status} ({sensor_data['power_voltage']:.1f}V) {gps_status} Speed: {sensor_data['speed_mph']:.1f} mph")
                    else:
                        print(f"📊 Recording... Power: {power_status} ({sensor_data['power_voltage']:.1f}V) {gps_status}")
                    self.save_telemetry_data(sensor_data)
                else:
                    power_status = "🔌 External" if sensor_data['on_external_power'] else "🔋 Battery"
                    gps_status = "🛰️ GPS" if sensor_data['gps_fix'] else "❌ No GPS"
                    print(f"⏸️  Standby... Power: {power_status} ({sensor_data['power_voltage']:.1f}V) {gps_status}")
                
                # Maintain sample rate
                elapsed = current_time - last_sample_time
                sleep_time = max(0, sample_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                last_sample_time = time.time()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(1)
        
        self.cleanup()
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    def cleanup(self):
        """Cleanup resources"""
        if self.engine_running:
            self.end_ride_session()
        if self.gps:
            try:
                self.gps.close()
            except:
                pass
        self.logger.info("🛑 Telemetry system stopped")

if __name__ == "__main__":
    telemetry = PowerBasedTelemetry()
    try:
        telemetry.main_loop()
    except KeyboardInterrupt:
        telemetry.logger.info("Interrupted by user")
    except Exception as e:
        telemetry.logger.error(f"Fatal error: {e}")
    finally:
        telemetry.cleanup() 