#!/usr/bin/env python3
"""
Cellular GPS Interface
Provides GPS data from SIM7600G-H cellular module via ModemManager
"""

import subprocess
import re
import time
import json
from datetime import datetime

class CellularGPS:
    def __init__(self):
        self.modem_id = 0
        self.last_fix = None
        
    def enable_gps(self):
        """Enable GPS on the cellular module"""
        try:
            # Enable modem
            subprocess.run(['sudo', 'mmcli', '-m', str(self.modem_id), '-e'], 
                         capture_output=True, check=True)
            time.sleep(2)
            
            # Enable GPS
            subprocess.run(['sudo', 'mmcli', '-m', str(self.modem_id), '--location-enable-gps-nmea'], 
                         capture_output=True, check=True)
            return True
        except Exception as e:
            print(f"Failed to enable GPS: {e}")
            return False
            
    def get_location(self):
        """Get current GPS location from cellular module"""
        try:
            result = subprocess.run(['sudo', 'mmcli', '-m', str(self.modem_id), '--location-get'], 
                                  capture_output=True, text=True, check=True)
            
            # Parse the output
            gps_data = self.parse_location_output(result.stdout)
            return gps_data
            
        except Exception as e:
            print(f"Failed to get location: {e}")
            return None
            
    def parse_location_output(self, output):
        """Parse ModemManager location output"""
        gps_data = {
            'latitude': None,
            'longitude': None,
            'speed_mph': 0,
            'heading': None,
            'gps_fix': False,
            'hdop': 99,
            'satellites_used': 0,
            'timestamp': datetime.now()
        }
        
        # Extract all NMEA sentences from the output
        nmea_lines = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            # Find lines that contain NMEA data (starting with $)
            if '$GP' in line or '$GN' in line or '$BD' in line or '$GL' in line:
                # Extract NMEA sentence - it might be after the pipe or mixed in
                nmea_matches = re.findall(r'\$[A-Z]{2}[A-Z,0-9\.\*\-]*', line)
                nmea_lines.extend(nmea_matches)
                
        # Parse NMEA sentences
        for nmea in nmea_lines:
            if nmea.startswith('$GPRMC') or nmea.startswith('$GNRMC'):
                parsed = self.parse_rmc(nmea)
                if parsed:
                    gps_data.update(parsed)
            elif nmea.startswith('$GPGGA') or nmea.startswith('$GNGGA'):
                parsed = self.parse_gga(nmea)
                if parsed:
                    gps_data.update(parsed)
                    
        return gps_data
        
    def parse_rmc(self, nmea):
        """Parse RMC NMEA sentence"""
        try:
            parts = nmea.split(',')
            if len(parts) < 10:
                return None
                
            status = parts[2]  # A = valid, V = invalid
            if status != 'A':
                return None
                
            lat = parts[3]
            lat_dir = parts[4]
            lon = parts[5]
            lon_dir = parts[6]
            speed_knots = parts[7] if parts[7] else '0'
            course = parts[8] if parts[8] else '0'
            
            if lat and lon and lat_dir and lon_dir:
                # Convert from NMEA format (DDMM.MMMMMM) to decimal degrees
                lat_float = float(lat)
                lat_deg = int(lat_float / 100)
                lat_min = lat_float % 100
                lat_decimal = lat_deg + lat_min / 60
                if lat_dir == 'S':
                    lat_decimal = -lat_decimal
                    
                lon_float = float(lon)
                lon_deg = int(lon_float / 100)
                lon_min = lon_float % 100
                lon_decimal = lon_deg + lon_min / 60
                if lon_dir == 'W':
                    lon_decimal = -lon_decimal
                    
                speed_mph = float(speed_knots) * 1.15078 if speed_knots else 0
                heading = float(course) if course else None
                
                return {
                    'latitude': lat_decimal,
                    'longitude': lon_decimal,
                    'speed_mph': speed_mph,
                    'heading': heading,
                    'gps_fix': True
                }
        except (ValueError, IndexError) as e:
            print(f"RMC parsing error: {e} for {nmea}")
            
        return None
        
    def parse_gga(self, nmea):
        """Parse GGA NMEA sentence"""
        try:
            parts = nmea.split(',')
            if len(parts) < 12:
                return None
                
            quality = parts[6]
            satellites = parts[7]
            hdop = parts[8]
            
            if quality and int(quality) > 0:
                return {
                    'satellites_used': int(satellites) if satellites else 0,
                    'hdop': float(hdop) if hdop else 99
                }
        except (ValueError, IndexError):
            pass
            
        return None
        
    def test_gps(self, duration=30):
        """Test GPS functionality"""
        print("🛰️ Testing Cellular GPS...")
        print(f"   Enabling GPS on modem {self.modem_id}...")
        
        if not self.enable_gps():
            print("   ❌ Failed to enable GPS")
            return False
            
        print(f"   Waiting for GPS fix (up to {duration} seconds)...")
        
        for i in range(duration):
            gps_data = self.get_location()
            if gps_data and gps_data['gps_fix']:
                print(f"   ✅ GPS Fix acquired!")
                print(f"   📍 Location: {gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}")
                print(f"   🛰️ Satellites: {gps_data['satellites_used']}")
                print(f"   📊 HDOP: {gps_data['hdop']}")
                print(f"   🏃 Speed: {gps_data['speed_mph']:.1f} mph")
                return True
            elif gps_data:
                print(f"   ⏳ Waiting... satellites: {gps_data['satellites_used']}")
            else:
                print(f"   ⏳ No GPS data yet...")
                
            time.sleep(1)
            
        print("   ⚠️ No GPS fix acquired within timeout")
        return False

if __name__ == "__main__":
    gps = CellularGPS()
    gps.test_gps() 