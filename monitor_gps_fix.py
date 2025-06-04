#!/usr/bin/env python3
"""
Monitor GPS until it gets a fix
Shows real-time progress of GPS acquisition
"""

import subprocess
import time
import re
from datetime import datetime

def run_command(cmd):
    """Run a command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                               text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

def parse_nmea_coordinates(nmea_data):
    """Parse coordinates from NMEA GPRMC sentence"""
    lines = nmea_data.split('\n')
    
    for line in lines:
        if '$GPRMC' in line or '$GNRMC' in line:
            parts = line.split(',')
            if len(parts) > 6 and parts[2] == 'A':  # A = Active (valid fix)
                try:
                    lat_raw = float(parts[3])
                    lat_dir = parts[4]
                    lon_raw = float(parts[5])
                    lon_dir = parts[6]
                    
                    # Convert from DDMM.MMMMM to DD.DDDDDD
                    lat_deg = int(lat_raw / 100)
                    lat_min = lat_raw % 100
                    latitude = lat_deg + lat_min / 60
                    if lat_dir == 'S':
                        latitude = -latitude
                        
                    lon_deg = int(lon_raw / 100)
                    lon_min = lon_raw % 100
                    longitude = lon_deg + lon_min / 60
                    if lon_dir == 'W':
                        longitude = -longitude
                    
                    return latitude, longitude, True
                    
                except (ValueError, IndexError):
                    continue
                    
    return None, None, False

def count_satellites(nmea_data):
    """Count satellites in view and used"""
    satellites_in_view = 0
    satellites_used = 0
    best_snr = 0
    
    lines = nmea_data.split('\n')
    
    # Count satellites in view from GSV sentences
    for line in lines:
        if '$GPGSV' in line or '$GLGSV' in line or '$BDGSV' in line:
            parts = line.split(',')
            if len(parts) > 3:
                try:
                    total_sats = int(parts[3])
                    satellites_in_view = max(satellites_in_view, total_sats)
                    
                    # Check signal strength (SNR) for satellites in this sentence
                    for i in range(4, len(parts), 4):
                        if i+3 < len(parts) and parts[i+3]:
                            try:
                                snr = int(parts[i+3])
                                best_snr = max(best_snr, snr)
                            except ValueError:
                                continue
                except ValueError:
                    continue
    
    # Count satellites used from GSA sentences
    for line in lines:
        if '$GPGSA' in line or '$GNGSA' in line or '$BDGSA' in line:
            parts = line.split(',')
            if len(parts) > 15 and parts[2] != '1':  # Mode 2=2D, 3=3D fix
                for sat_id in parts[3:15]:
                    if sat_id:
                        satellites_used += 1
                        
    return satellites_in_view, satellites_used, best_snr

def monitor_gps(duration=600):  # 10 minutes default
    """Monitor GPS for a fix"""
    print("🛰️  GPS Fix Monitor")
    print("==================")
    print(f"Monitoring for {duration} seconds...")
    print("Looking for GPS fix...\n")
    
    start_time = time.time()
    fix_found = False
    
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Get GPS data
        gps_data = run_command("sudo mmcli -m 0 --location-get")
        
        if "GPS" in gps_data and "nmea:" in gps_data:
            # Extract just the NMEA part
            nmea_start = gps_data.find("nmea:")
            nmea_data = gps_data[nmea_start+5:]
            
            # Parse coordinates
            lat, lon, has_fix = parse_nmea_coordinates(nmea_data)
            
            # Count satellites
            sats_in_view, sats_used, best_snr = count_satellites(nmea_data)
            
            print(f"[{current_time}] {elapsed:3d}s | ", end="")
            
            if has_fix:
                print(f"🎉 GPS FIX! Lat: {lat:.6f}°, Lon: {lon:.6f}° | ", end="")
                fix_found = True
            else:
                print(f"⏳ Searching... | ", end="")
            
            print(f"Sats: {sats_in_view} in view, {sats_used} used | Best SNR: {best_snr}")
            
            if has_fix:
                print(f"\n✅ SUCCESS! GPS fix obtained after {elapsed} seconds")
                print(f"📍 Location: {lat:.6f}, {lon:.6f}")
                break
        else:
            print(f"[{current_time}] {elapsed:3d}s | ❌ No GPS data available")
            
        time.sleep(5)
    
    if not fix_found:
        print(f"\n⚠️  No GPS fix after {duration} seconds")
        print("💡 GPS is receiving satellites but needs more time or better conditions")
        print("Try:")
        print("1. Move to area with clearer sky view")
        print("2. Wait longer (GPS cold start can take 5-15 minutes)")
        print("3. Check antenna connections")
    
    return fix_found

if __name__ == "__main__":
    try:
        print("Starting GPS monitoring...")
        print("Press Ctrl+C to stop\n")
        
        fix_found = monitor_gps(duration=900)  # Monitor for 15 minutes
        
        if fix_found:
            print("\n🎉 GPS is working! You can now use it in your telemetry system.")
        else:
            print("\n📡 GPS is configured but may need more time to acquire fix.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}") 