#!/usr/bin/env python3
"""
GPS Debug Script - Find and fix GPS connection issues
"""

import subprocess
import time
import os
import json
from gps3 import gps3

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "Timeout", 1

def check_usb_devices():
    """Check USB connected devices"""
    print("🔍 USB DEVICES:")
    stdout, stderr, code = run_command("lsusb | grep -i 'u-blox\\|gps\\|1546:'")
    if stdout:
        print(f"   ✅ GPS Device: {stdout}")
        return True
    else:
        print("   ❌ No GPS device found in USB")
        return False

def check_serial_ports():
    """Check available serial ports"""
    print("\n📱 SERIAL PORTS:")
    ports = []
    for port in ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyUSB0', '/dev/ttyUSB1']:
        if os.path.exists(port):
            stat = os.stat(port)
            print(f"   ✅ {port} (modified: {time.ctime(stat.st_mtime)})")
            ports.append(port)
        else:
            print(f"   ❌ {port} - not found")
    return ports

def check_gpsd_status():
    """Check GPSD daemon status"""
    print("\n🛰️ GPSD STATUS:")
    
    # Check if gpsd is running
    stdout, stderr, code = run_command("ps aux | grep gpsd | grep -v grep")
    if code == 0 and stdout:
        print(f"   ✅ GPSD Running: {stdout}")
        
        # Extract the device from ps output
        if '/dev/tty' in stdout:
            device = stdout.split('/dev/')[1].split()[0]
            device = f"/dev/{device}"
            print(f"   📡 Using device: {device}")
            return device
    else:
        print("   ❌ GPSD not running")
        return None

def test_gps_data():
    """Test GPS data using gps3"""
    print("\n📡 TESTING GPS DATA:")
    try:
        gps_socket = gps3.GPSDSocket()
        gps_socket.connect()
        gps_socket.watch()
        data_stream = gps3.DataStream()
        
        print("   🔄 Reading GPS data for 10 seconds...")
        
        for i in range(50):  # 10 seconds at 0.2 second intervals
            new_data = gps_socket.next(timeout=0.2)
            if new_data:
                data_stream.unpack(new_data)
                
                # Print any received data
                if hasattr(data_stream, 'TPV') and data_stream.TPV:
                    tpv = data_stream.TPV
                    if 'lat' in tpv and 'lon' in tpv:
                        lat = tpv.get('lat', 'n/a')
                        lon = tpv.get('lon', 'n/a')
                        mode = tpv.get('mode', 'n/a')
                        print(f"   📍 Fix Mode: {mode}, Lat: {lat}, Lon: {lon}")
                        
                        if lat != 'n/a' and lon != 'n/a' and lat != 0 and lon != 0:
                            print("   ✅ REAL GPS COORDINATES FOUND!")
                            return True
            
            time.sleep(0.2)
        
        print("   ⚠️  No valid GPS coordinates received in 10 seconds")
        return False
        
    except Exception as e:
        print(f"   ❌ GPS Test Error: {e}")
        return False

def restart_gpsd_with_correct_port():
    """Try to restart GPSD with the correct port"""
    print("\n🔧 FIXING GPS CONNECTION:")
    
    # Stop gpsd
    print("   🛑 Stopping GPSD...")
    run_command("sudo systemctl stop gpsd")
    run_command("sudo systemctl stop gpsd.socket")
    run_command("sudo killall gpsd")
    time.sleep(2)
    
    # Find the GPS device
    ports = check_serial_ports()
    gps_port = None
    
    # Check which port has a U-Blox device
    for port in ports:
        try:
            # Check device info
            stdout, stderr, code = run_command(f"udevadm info --name={port} | grep ID_VENDOR_ID")
            if "1546" in stdout:  # U-Blox vendor ID
                gps_port = port
                print(f"   ✅ Found U-Blox GPS on {port}")
                break
        except:
            pass
    
    if not gps_port and ports:
        # Try the most recently modified port
        gps_port = max(ports, key=lambda p: os.stat(p).st_mtime)
        print(f"   🔍 Trying most recent port: {gps_port}")
    
    if gps_port:
        print(f"   🚀 Starting GPSD on {gps_port}")
        run_command(f"sudo gpsd -n {gps_port}")
        time.sleep(3)
        return gps_port
    else:
        print("   ❌ No suitable GPS port found")
        return None

def main():
    """Main GPS debugging function"""
    print("🛰️ GPS CONNECTION DEBUGGER")
    print("=" * 50)
    
    # Step 1: Check hardware
    usb_ok = check_usb_devices()
    if not usb_ok:
        print("\n❌ GPS hardware not detected. Check USB connection!")
        return
    
    # Step 2: Check serial ports
    ports = check_serial_ports()
    if not ports:
        print("\n❌ No serial ports found. Hardware issue!")
        return
    
    # Step 3: Check GPSD
    current_device = check_gpsd_status()
    
    # Step 4: Test current GPS data
    gps_working = test_gps_data()
    
    if gps_working:
        print("\n🎉 GPS IS WORKING CORRECTLY!")
        print("   The issue might be in your telemetry script.")
        print("   Try restarting your motorcycle-telemetry.service")
        return
    
    # Step 5: Try to fix GPS connection
    print("\n🔧 GPS not getting valid data. Attempting fix...")
    fixed_port = restart_gpsd_with_correct_port()
    
    if fixed_port:
        print("\n🔄 Testing GPS after fix...")
        time.sleep(5)
        if test_gps_data():
            print("\n🎉 GPS FIXED!")
            print(f"   ✅ GPS working on {fixed_port}")
            print("   🔄 Restart your telemetry service:")
            print("   sudo systemctl restart motorcycle-telemetry.service")
        else:
            print("\n⚠️  GPS still not working. Possible issues:")
            print("   • GPS needs clear sky view (go outdoors)")
            print("   • GPS needs 2-3 minutes to acquire satellites")
            print("   • Hardware problem with GPS puck")
            print("   • Try unplugging/replugging GPS puck")
    else:
        print("\n❌ Could not fix GPS connection automatically")

if __name__ == "__main__":
    main() 