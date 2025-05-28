#!/usr/bin/env python3
"""
Comprehensive GPS Debugging Tool
Checks all aspects of GPS system on the motorcycle
"""

import os
import sys
import time
import json
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def print_header(text):
    """Print a section header"""
    print("\n" + "="*60)
    print(f" 🔍 {text}")
    print("="*60)

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                               text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def check_gpsd_running():
    """Check if the GPS daemon is running"""
    print_header("CHECKING GPS DAEMON (gpsd)")
    
    # Check if gpsd is running
    gpsd_status = run_command("systemctl is-active gpsd")
    print(f"GPSD Service Status: {gpsd_status}")
    
    # Get more details if it's running
    if gpsd_status == "active":
        print("\n📊 GPSD Service Details:")
        print(run_command("systemctl status gpsd | grep Active"))
        
        # Check GPSD devices
        devices = run_command("gpsd -l")
        print(f"\n🔌 GPSD Configured Devices: {devices}")
        
        # Check if GPSD is responding
        clients = run_command("pgrep -a gpsd")
        print(f"GPSD Processes: {clients}")
    else:
        print("❌ GPSD is not active - this is the likely cause of GPS issues")
        print("Run: sudo systemctl start gpsd")

def check_usb_gps():
    """Check for USB GPS devices"""
    print_header("CHECKING USB GPS DEVICES")
    
    # List USB devices
    usb_devices = run_command("lsusb")
    print("USB Devices:")
    print(usb_devices)
    
    # Check for USB serial devices that might be GPS
    serial_devices = run_command("ls -l /dev/tty*")
    print("\nSerial Devices:")
    print(serial_devices)
    
    # Look for typical GPS devices
    gps_candidates = []
    for line in serial_devices.split('\n'):
        if "USB" in line and ("ACM" in line or "ttyS" in line or "ttyUSB" in line):
            gps_candidates.append(line)
    
    if gps_candidates:
        print("\n🛰️ Potential GPS devices:")
        for device in gps_candidates:
            print(device)
    else:
        print("\n❌ No obvious USB GPS devices found")

def check_motorcycle_telemetry():
    """Check the motorcycle telemetry service"""
    print_header("CHECKING MOTORCYCLE TELEMETRY SERVICE")
    
    # Check if the service is running
    telemetry_status = run_command("systemctl is-active motorcycle-telemetry")
    print(f"Telemetry Service Status: {telemetry_status}")
    
    if telemetry_status == "active":
        print("\n📊 Telemetry Service Details:")
        print(run_command("systemctl status motorcycle-telemetry | grep Active"))
        
        # Check recent logs
        print("\n📋 Recent Telemetry Logs:")
        logs = run_command("tail -n 15 /home/pi/motorcycle_data/telemetry.log")
        print(logs)
        
        # Look for GPS-related messages in logs
        gps_logs = run_command("grep -i gps /home/pi/motorcycle_data/telemetry.log | tail -n 10")
        print("\n📡 Recent GPS-related log entries:")
        print(gps_logs)
    else:
        print("❌ Motorcycle telemetry service is not active")
        print("Run: sudo systemctl start motorcycle-telemetry")

def check_database():
    """Check GPS data in the database"""
    print_header("CHECKING GPS DATA IN DATABASE")
    
    try:
        db_path = Path("/home/pi/motorcycle_data/telemetry.db")
        
        if not db_path.exists():
            print(f"❌ Database not found at {db_path}")
            return
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check total records
        cursor.execute("SELECT COUNT(*) FROM telemetry_data")
        total_records = cursor.fetchone()[0]
        print(f"Total records in database: {total_records}")
        
        # Check recent GPS data
        recent_time = datetime.now() - timedelta(hours=1)
        cursor.execute("""
            SELECT timestamp, latitude, longitude, gps_fix, satellites_used
            FROM telemetry_data 
            WHERE timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        """, (recent_time.isoformat(),))
        
        records = cursor.fetchall()
        print(f"\nRecent GPS records (last hour): {len(records)}")
        
        if records:
            print("\nLatest GPS readings:")
            for record in records:
                time_str = record[0]
                lat = record[1] if record[1] is not None else "None"
                lon = record[2] if record[2] is not None else "None"
                fix = "Yes" if record[3] else "No"
                sats = record[4] if record[4] is not None else "Unknown"
                
                print(f"Time: {time_str}, Lat: {lat}, Lon: {lon}, Fix: {fix}, Satellites: {sats}")
                
            # Check for valid GPS readings
            valid_gps = False
            for record in records:
                if record[1] is not None and record[2] is not None:
                    if record[1] != 0 and record[2] != 0:
                        valid_gps = True
                        break
                        
            if valid_gps:
                print("\n✅ Valid GPS coordinates found in recent data")
            else:
                print("\n❌ No valid GPS coordinates found in recent data")
        else:
            print("❌ No recent GPS records found")
            
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

def try_direct_gps_access():
    """Try to directly access GPS data"""
    print_header("TRYING DIRECT GPS ACCESS")
    
    try:
        print("Attempting to directly read from GPS daemon...")
        print("This will run for 10 seconds, looking for GPS data.")
        
        # Import gps module
        try:
            from gps3 import gps3
            print("✅ Successfully imported GPS module")
        except ImportError:
            print("❌ Could not import GPS module. Is gps3 installed?")
            print("Try: pip install gps3")
            return
            
        # Connect to GPSD
        try:
            gps_socket = gps3.GPSDSocket()
            data_stream = gps3.DataStream()
            gps_socket.connect()
            gps_socket.watch()
            print("✅ Successfully connected to GPS daemon")
        except Exception as e:
            print(f"❌ Failed to connect to GPS daemon: {e}")
            return
            
        # Try to get data for 10 seconds
        print("\nListening for GPS data for 10 seconds...")
        start_time = time.time()
        gps_data_received = False
        valid_fix = False
        
        while time.time() - start_time < 10:
            for new_data in gps_socket:
                if new_data:
                    data_stream.unpack(new_data)
                    gps_data_received = True
                    
                    if hasattr(data_stream, 'TPV'):
                        tpv = data_stream.TPV
                        if isinstance(tpv, dict):
                            print(f"\nReceived GPS data: {json.dumps(tpv, indent=2)}")
                            
                            if 'lat' in tpv and 'lon' in tpv and tpv['lat'] != 'n/a' and tpv['lon'] != 'n/a':
                                valid_fix = True
                                print(f"✅ VALID GPS FIX DETECTED!")
                                print(f"Latitude: {tpv['lat']}, Longitude: {tpv['lon']}")
                                if 'speed' in tpv and tpv['speed'] != 'n/a':
                                    print(f"Speed: {float(tpv['speed']) * 2.237:.1f} mph")
                                break
                            
            if valid_fix:
                break
                
            time.sleep(0.1)
            
        if not gps_data_received:
            print("❌ No GPS data received within 10 seconds")
        elif not valid_fix:
            print("⚠️ GPS data received but no valid fix (no coordinates)")
            print("This usually means the GPS needs more time to acquire satellites")
            print("It can take up to 5 minutes outdoors to get a fix")
            
    except Exception as e:
        print(f"Error trying direct GPS access: {e}")

def fix_common_issues():
    """Attempt to fix common GPS issues"""
    print_header("ATTEMPTING TO FIX COMMON GPS ISSUES")
    
    print("1. Checking GPSD configuration...")
    gpsd_conf = run_command("cat /etc/default/gpsd 2>/dev/null || echo 'Not found'")
    if "Not found" in gpsd_conf:
        print("❌ GPSD configuration not found")
    else:
        print("GPSD Configuration:")
        print(gpsd_conf)
    
    print("\n2. Trying to restart GPSD...")
    restart_result = run_command("sudo systemctl restart gpsd")
    print(f"GPSD restart result: {'Success' if restart_result == '' else restart_result}")
    
    print("\n3. Restarting motorcycle telemetry service...")
    telemetry_restart = run_command("sudo systemctl restart motorcycle-telemetry")
    print(f"Telemetry restart result: {'Success' if telemetry_restart == '' else telemetry_restart}")
    
    print("\n4. Waiting 5 seconds for services to initialize...")
    time.sleep(5)
    
    print("\n5. Checking GPS status after restart...")
    gpsd_status = run_command("systemctl is-active gpsd")
    telemetry_status = run_command("systemctl is-active motorcycle-telemetry")
    print(f"GPSD Service Status: {gpsd_status}")
    print(f"Telemetry Service Status: {telemetry_status}")
    
    if gpsd_status == "active" and telemetry_status == "active":
        print("\n✅ Both services are running")
        print("GPS may need a few minutes to acquire satellites.")
        print("Try going outside with a clear view of the sky and wait 5-10 minutes.")
    else:
        print("\n❌ One or both services are still not running correctly")

def main():
    """Main function"""
    print("\n🛰️ MOTORCYCLE GPS TROUBLESHOOTER")
    print("================================")
    print("This tool will help diagnose GPS issues with your motorcycle telemetry system.")
    print("Running comprehensive checks...")
    
    check_gpsd_running()
    check_usb_gps()
    check_motorcycle_telemetry()
    check_database()
    try_direct_gps_access()
    fix_common_issues()
    
    print_header("SUMMARY & RECOMMENDATIONS")
    print("""
WHAT TO DO NEXT:
1. Make sure your GPS has a clear view of the sky
2. Check that your GPS device is properly connected
3. Wait 5-10 minutes for the GPS to acquire satellites
4. Refresh your dashboard at http://localhost:1880/ui

If problems persist:
- Check if your GPS device is recognized (should be at /dev/ttyACM0 or similar)
- Verify GPSD configuration in /etc/default/gpsd 
- Ensure GPSD is using the correct device
- Check telemetry logs for GPS-related errors
    """)

if __name__ == "__main__":
    main() 