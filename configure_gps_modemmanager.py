#!/usr/bin/env python3
"""
Configure GPS using ModemManager for SIM7600G-H
This properly enables GPS and tests for a fix
"""

import subprocess
import time
import json
import re

def run_command(cmd):
    """Run a command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                               text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"

def get_modem_info():
    """Get modem information"""
    print("🔍 Getting modem information...")
    
    # List modems
    modems = run_command("sudo mmcli -L")
    print(f"Available modems: {modems}")
    
    # Get modem 0 info
    info = run_command("sudo mmcli -m 0")
    print(f"Modem details:\n{info}")
    
    return True

def configure_gps():
    """Configure GPS location services"""
    print("\n🛰️ Configuring GPS location services...")
    
    # Enable all GPS capabilities
    print("Enabling GPS raw data...")
    result = run_command("sudo mmcli -m 0 --location-enable-gps-raw")
    print(f"GPS Raw: {result}")
    
    print("Enabling GPS NMEA...")
    result = run_command("sudo mmcli -m 0 --location-enable-gps-nmea")
    print(f"GPS NMEA: {result}")
    
    print("Enabling A-GPS MSA...")
    result = run_command("sudo mmcli -m 0 --location-enable-agps-msa")
    print(f"A-GPS MSA: {result}")
    
    print("Enabling A-GPS MSB...")
    result = run_command("sudo mmcli -m 0 --location-enable-agps-msb")
    print(f"A-GPS MSB: {result}")
    
    # Check status
    print("\nChecking GPS status...")
    status = run_command("sudo mmcli -m 0 --location-status")
    print(f"GPS Status:\n{status}")
    
    return True

def test_gps_fix(duration=180):
    """Test for GPS fix over specified duration"""
    print(f"\n📡 Testing GPS for {duration} seconds...")
    print("Looking for GPS fix... (may take several minutes for cold start)")
    
    start_time = time.time()
    fix_found = False
    best_lat = None
    best_lon = None
    
    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        
        # Get location data
        location_data = run_command("sudo mmcli -m 0 --location-get")
        
        print(f"\n⏱️  Time: {elapsed}s/{duration}s")
        
        if "GPS" in location_data and "nmea:" in location_data:
            # Parse NMEA data for coordinates
            lines = location_data.split('\n')
            for line in lines:
                if '$GPRMC' in line or '$GNRMC' in line:
                    # GPRMC format: $GPRMC,time,status,lat,lat_dir,lon,lon_dir,speed,course,date,,,*checksum
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
                            
                            print(f"🎉 GPS FIX FOUND!")
                            print(f"   📍 Latitude: {latitude:.6f}°")
                            print(f"   📍 Longitude: {longitude:.6f}°")
                            print(f"   ⏰ Time to fix: {elapsed} seconds")
                            
                            best_lat = latitude
                            best_lon = longitude
                            fix_found = True
                            break
                            
                        except (ValueError, IndexError):
                            continue
                            
                elif '$GPGGA' in line or '$GNGGA' in line:
                    # Parse GGA for fix quality
                    parts = line.split(',')
                    if len(parts) > 6:
                        fix_quality = parts[6] if parts[6] else "0"
                        satellites = parts[7] if parts[7] else "0"
                        if fix_quality != "0":
                            print(f"   🛰️  Fix Quality: {fix_quality}, Satellites: {satellites}")
        
        if fix_found:
            break
            
        # Show satellites being tracked
        if "GPS" in location_data:
            # Count satellite references in NMEA
            sat_count = location_data.count('$GPGSV') + location_data.count('$GLGSV') + location_data.count('$BDGSV')
            if sat_count > 0:
                print(f"   🛰️  Tracking satellites...")
            else:
                print(f"   ⏳ Searching for satellites...")
        
        time.sleep(5)
    
    if not fix_found:
        print(f"\n❌ No GPS fix obtained in {duration} seconds")
        print("💡 Troubleshooting tips:")
        print("1. Ensure clear view of sky (no buildings/trees)")
        print("2. GPS cold start can take 5-15 minutes")
        print("3. Try again in a different location")
        print("4. Check antenna connections")
    else:
        print(f"\n✅ GPS is working! Best fix: {best_lat:.6f}, {best_lon:.6f}")
        
    return fix_found, best_lat, best_lon

def update_telemetry_config(lat, lon):
    """Update telemetry configuration with working GPS"""
    print(f"\n⚙️  Updating telemetry configuration...")
    
    # Create a GPS test result file
    gps_config = {
        "gps_working": True,
        "test_location": {
            "latitude": lat,
            "longitude": lon,
            "timestamp": time.time()
        },
        "modem_gps_enabled": True,
        "gps_source": "ModemManager",
        "device": "/dev/ttyUSB1"
    }
    
    with open('/home/pi/gps_test_results.json', 'w') as f:
        json.dump(gps_config, f, indent=2)
        
    print("✅ GPS configuration saved to gps_test_results.json")

def main():
    print("🛰️ SIM7600G-H GPS Configuration via ModemManager")
    print("================================================")
    
    try:
        # Get modem info
        get_modem_info()
        
        # Configure GPS
        configure_gps()
        
        # Test for GPS fix
        fix_found, lat, lon = test_gps_fix(duration=300)  # Test for 5 minutes
        
        if fix_found:
            print("\n🎉 SUCCESS! GPS is working properly!")
            update_telemetry_config(lat, lon)
            
            print("\n📝 Next steps:")
            print("1. Update your telemetry script to use ModemManager GPS")
            print("2. Use 'sudo mmcli -m 0 --location-get' in your code")
            print("3. GPS data is available through NMEA parsing")
            print("4. Restart your dashboard services")
            
        else:
            print("\n⚠️  GPS configuration complete but no fix yet")
            print("The GPS is enabled but may need more time or better conditions")
            
        # Show final status
        print("\n📊 Final GPS Status:")
        status = run_command("sudo mmcli -m 0 --location-status")
        print(status)
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 