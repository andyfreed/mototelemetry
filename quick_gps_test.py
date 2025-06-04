#!/usr/bin/env python3
"""
Quick GPS fix test - aggressive approach
"""

import subprocess
import time
import re

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
        return result.stdout.strip()
    except:
        return None

def parse_gps_data():
    """Get current GPS status"""
    data = run_cmd("sudo mmcli -m 0 --location-get")
    if not data:
        return None, 0, 0, 0
    
    # Parse NMEA for fix status
    has_fix = False
    lat, lon = None, None
    
    if '$GPRMC' in data:
        lines = data.split('\n')
        for line in lines:
            if '$GPRMC' in line:
                parts = line.split(',')
                if len(parts) > 6 and parts[2] == 'A':  # Active fix
                    has_fix = True
                    try:
                        lat_raw = float(parts[3])
                        lat_dir = parts[4]
                        lon_raw = float(parts[5])
                        lon_dir = parts[6]
                        
                        # Convert DDMM.MMMMM to DD.DDDDDD
                        lat_deg = int(lat_raw / 100)
                        lat_min = lat_raw % 100
                        lat = lat_deg + lat_min / 60
                        if lat_dir == 'S':
                            lat = -lat
                            
                        lon_deg = int(lon_raw / 100)
                        lon_min = lon_raw % 100
                        lon = lon_deg + lon_min / 60
                        if lon_dir == 'W':
                            lon = -lon
                    except:
                        pass
                break
    
    # Count satellites
    gps_sats = data.count('$GPGSV')
    glo_sats = data.count('$GLGSV') 
    bds_sats = data.count('$BDGSV')
    
    return (lat, lon) if has_fix else None, gps_sats, glo_sats, bds_sats

def quick_test():
    print("🚀 QUICK GPS FIX TEST")
    print("====================")
    
    # Test 1: Current status
    print("📍 Current GPS Status:")
    coords, gps, glo, bds = parse_gps_data()
    if coords:
        print(f"✅ GPS FIX FOUND! {coords[0]:.6f}, {coords[1]:.6f}")
        return True
    else:
        print(f"⏳ Searching... GPS:{gps} GLO:{glo} BDS:{bds} sentences")
    
    # Test 2: Fast retry with status
    print("\n🔄 Fast retry test (30 seconds)...")
    for i in range(6):
        time.sleep(5)
        coords, gps, glo, bds = parse_gps_data()
        
        if coords:
            print(f"🎉 GPS FIX! {coords[0]:.6f}, {coords[1]:.6f} (after {(i+1)*5}s)")
            return True
        else:
            print(f"   {(i+1)*5:2d}s: Sats GPS:{gps} GLO:{glo} BDS:{bds}")
    
    print("\n💡 TROUBLESHOOTING:")
    print("1. Are you OUTDOORS with clear sky view?")
    print("2. GPS cold start can take 5-15 minutes")
    print("3. Try moving to different location")
    print("4. Check that device isn't covered/blocked")
    
    return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 SUCCESS! GPS is working!")
        print("Now your telemetry system can use GPS coordinates!")
    else:
        print(f"\n⏱️  No fix yet, but GPS is tracking satellites")
        print("📱 Try running this outdoors with clear sky view") 