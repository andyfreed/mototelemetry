#!/usr/bin/env python3
"""
Simple GPS test script
Tests GPS functionality using multiple methods
"""

import os
import time
import sys
import subprocess
from datetime import datetime

print("🛰️ GPS Test Script")
print("=================")
print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Step 1: Check if gpsd is running
print("\n1. Checking if gpsd is running...")
try:
    result = subprocess.run(['systemctl', 'status', 'gpsd'], capture_output=True, text=True)
    is_active = 'Active: active' in result.stdout
    print(f"GPSD Service active: {is_active}")
    
    # Extract some details from status
    for line in result.stdout.split('\n'):
        if 'Active:' in line or 'CGroup:' in line:
            print(f"  {line.strip()}")
except Exception as e:
    print(f"Error checking gpsd status: {e}")

# Step 2: Check for GPS devices
print("\n2. Checking for GPS devices...")
try:
    usb_result = subprocess.run(['lsusb'], capture_output=True, text=True)
    print("USB Devices:")
    for line in usb_result.stdout.split('\n'):
        if any(x in line.lower() for x in ['gps', 'u-blox']):
            print(f"  ✅ {line}")
        
    tty_result = subprocess.run(['ls', '-l', '/dev/ttyACM*'], capture_output=True, text=True)
    print("Serial Devices:")
    print(tty_result.stdout)
except Exception as e:
    print(f"Error checking devices: {e}")

# Step 3: Try using gps3 library
print("\n3. Trying to get GPS data using gps3 library...")
try:
    # First check if we can import the library
    import importlib
    gps3_spec = importlib.util.find_spec("gps3")
    if gps3_spec is None:
        print("❌ gps3 library not found. Check installation.")
    else:
        print("✅ gps3 library is installed")
        
        from gps3 import gps3
        print("✅ Successfully imported gps3 module")
        
        # Try to connect to gpsd
        print("Connecting to gpsd...")
        gps_socket = gps3.GPSDSocket()
        data_stream = gps3.DataStream()
        gps_socket.connect()
        gps_socket.watch()
        print("✅ Connected to gpsd")
        
        # Try to get data for 10 seconds
        print("Waiting for GPS data (10 seconds)...")
        start_time = time.time()
        count = 0
        fix_found = False
        
        while time.time() - start_time < 10:
            for new_data in gps_socket:
                if new_data:
                    count += 1
                    data_stream.unpack(new_data)
                    
                    if hasattr(data_stream, 'TPV'):
                        tpv = data_stream.TPV
                        if isinstance(tpv, dict):
                            status = "⏳ Waiting for fix"
                            if 'mode' in tpv:
                                mode = tpv.get('mode', 0)
                                if mode >= 2:
                                    status = "✅ GPS FIX OBTAINED"
                                    fix_found = True
                                    
                            print(f"\rPackets: {count} | Status: {status}", end="")
                            
                            if fix_found and 'lat' in tpv and 'lon' in tpv and tpv['lat'] != 'n/a':
                                print(f"\n✅ Position: Lat {tpv['lat']}, Lon {tpv['lon']}")
                                if 'speed' in tpv and tpv['speed'] != 'n/a':
                                    print(f"  Speed: {float(tpv['speed']) * 2.237:.1f} mph")
                                break
                time.sleep(0.1)
                
            if fix_found:
                break
                
        print(f"\nReceived {count} data packets from gpsd")
        if not fix_found:
            print("⚠️ No GPS fix obtained in 10 seconds. This is normal for cold starts.")
            print("  GPS may need up to 5 minutes outside to get a fix.")
    
except ImportError:
    print("❌ Could not import gps3. Check if the package is installed.")
except Exception as e:
    print(f"❌ Error testing GPS with gps3: {e}")

# Step 4: Try direct gpsd query with subprocess
print("\n4. Trying direct gpsd query with gpspipe...")
try:
    print("Running gpspipe for 5 seconds...")
    gpspipe = subprocess.run(['gpspipe', '-w', '-n', '10'], capture_output=True, text=True, timeout=5)
    if gpspipe.returncode == 0:
        print("✅ Received data from gpspipe:")
        for line in gpspipe.stdout.split('\n')[:5]:  # Show first 5 lines
            print(f"  {line}")
    else:
        print(f"❌ gpspipe error: {gpspipe.stderr}")
except subprocess.TimeoutExpired:
    print("⚠️ gpspipe timeout - possibly waiting for data")
except Exception as e:
    print(f"❌ Error running gpspipe: {e}")

# Step 5: Manually check if device is responding
print("\n5. Testing direct serial communication with GPS device...")
try:
    if os.path.exists('/dev/ttyACM0'):
        print("✅ Found /dev/ttyACM0")
        # Try to read directly from the device
        print("Attempting to read NMEA sentences directly...")
        with open('/dev/ttyACM0', 'rb') as f:
            f.timeout = 2
            data = f.read(1024)
            if data:
                print(f"✅ Device is sending data! First 100 bytes: {data[:100]}")
            else:
                print("❌ No data received from device")
    else:
        print("❌ Device /dev/ttyACM0 not found")
except Exception as e:
    print(f"❌ Error reading from device: {e}")

# Final summary
print("\n🧪 GPS TEST SUMMARY")
print("=================")
print("If you're not getting a GPS fix:")
print("1. Make sure you're outdoors with clear sky view")
print("2. Wait up to 5 minutes for a cold start")
print("3. Check USB connections")
print("4. Try running 'sudo ./fix_gps.sh'") 