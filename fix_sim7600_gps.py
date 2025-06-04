#!/usr/bin/env python3
"""
Fix GPS configuration for SIM7600G-H cellular module
This script directly configures GPS via AT commands
"""

import serial
import time
import sys
import re

class SIM7600GPS:
    def __init__(self):
        self.ser = None
        self.port = None
        
    def find_at_port(self):
        """Find the AT command port for SIM7600G-H"""
        # Try common SIM7600 AT ports
        ports = ['/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB1', '/dev/ttyUSB0']
        
        for port in ports:
            try:
                print(f"Testing {port}...")
                ser = serial.Serial(port, 115200, timeout=3)
                time.sleep(0.5)
                
                # Clear buffers
                ser.flushInput()
                ser.flushOutput()
                
                # Test AT command
                ser.write(b'AT\r\n')
                time.sleep(1)
                response = ser.read(200).decode('utf-8', errors='ignore')
                
                if 'OK' in response:
                    print(f"✅ Found AT port: {port}")
                    self.ser = ser
                    self.port = port
                    return True
                    
                ser.close()
                
            except Exception as e:
                print(f"❌ Error on {port}: {e}")
                continue
                
        return False
        
    def send_at(self, command, timeout=5, expect_ok=True):
        """Send AT command and return response"""
        if not self.ser:
            return None
            
        try:
            # Clear input buffer
            self.ser.flushInput()
            
            # Send command
            self.ser.write(f'{command}\r\n'.encode())
            
            # Read response
            start_time = time.time()
            response = ''
            
            while time.time() - start_time < timeout:
                if self.ser.in_waiting:
                    chunk = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    response += chunk
                    
                    # Check if we got a complete response
                    if expect_ok and ('OK' in response or 'ERROR' in response):
                        break
                    elif not expect_ok and response.count('\n') >= 2:
                        break
                        
                time.sleep(0.1)
                
            return response.strip()
            
        except Exception as e:
            print(f"Error sending AT command: {e}")
            return None
            
    def check_gps_status(self):
        """Check current GPS status"""
        print("\n🔍 Checking GPS status...")
        
        # Check GPS power
        response = self.send_at('AT+CGPS?')
        print(f"GPS Power Status: {response}")
        
        # Check GPS info
        response = self.send_at('AT+CGPSINFO')
        print(f"GPS Info: {response}")
        
        return response
        
    def enable_gps(self):
        """Enable and configure GPS"""
        print("\n🛰️ Enabling GPS...")
        
        # Turn off GPS first (in case it's already on)
        print("Turning off GPS...")
        self.send_at('AT+CGPS=0', timeout=10)
        time.sleep(2)
        
        # Turn on GPS
        print("Turning on GPS...")
        response = self.send_at('AT+CGPS=1', timeout=10)
        print(f"GPS Enable: {response}")
        
        if 'OK' not in response:
            print("❌ Failed to enable GPS")
            return False
            
        # Set GPS mode to standalone (no network assistance for now)
        print("Setting GPS mode to standalone...")
        response = self.send_at('AT+CGPSMODE=1', timeout=5)
        print(f"GPS Mode: {response}")
        
        # Set GPS constellation (GPS + GLONASS + BeiDou)
        print("Setting GPS constellation...")
        response = self.send_at('AT+CGPSCNST=7', timeout=5)  # 1=GPS, 2=GLO, 4=BDS, 7=ALL
        print(f"GPS Constellation: {response}")
        
        # Set GPS reset mode (cold start for better accuracy)
        print("Setting GPS to cold start...")
        response = self.send_at('AT+CGPSRST=1', timeout=10)
        print(f"GPS Reset: {response}")
        
        return True
        
    def test_gps_data(self, duration=60):
        """Test GPS data acquisition"""
        print(f"\n📡 Testing GPS data for {duration} seconds...")
        print("Looking for GPS fix... (this may take several minutes outdoors)")
        
        start_time = time.time()
        fix_found = False
        
        while time.time() - start_time < duration:
            # Get GPS info
            response = self.send_at('AT+CGPSINFO', timeout=3, expect_ok=False)
            
            if response and '+CGPSINFO:' in response:
                # Parse GPS info
                gps_line = None
                for line in response.split('\n'):
                    if '+CGPSINFO:' in line:
                        gps_line = line
                        break
                        
                if gps_line:
                    # Format: +CGPSINFO: lat,N/S,lon,E/W,date,UTC time,alt,speed,course
                    parts = gps_line.split(':')[1].strip().split(',')
                    
                    if len(parts) >= 9 and parts[0] != '':
                        lat = parts[0]
                        lat_dir = parts[1] 
                        lon = parts[2]
                        lon_dir = parts[3]
                        date = parts[4]
                        time_str = parts[5]
                        
                        if lat and lon and lat != '' and lon != '':
                            print(f"📍 GPS FIX FOUND!")
                            print(f"   Latitude: {lat}°{lat_dir}")
                            print(f"   Longitude: {lon}°{lon_dir}")
                            print(f"   Date: {date}")
                            print(f"   Time: {time_str}")
                            fix_found = True
                            break
                    else:
                        elapsed = int(time.time() - start_time)
                        print(f"⏳ Searching for satellites... ({elapsed}s/{duration}s)")
                        
            time.sleep(5)
            
        if not fix_found:
            print("❌ No GPS fix obtained in the test period")
            print("💡 Try leaving the device outside with clear sky view for longer")
            
        return fix_found
        
    def get_nmea_data(self):
        """Get NMEA GPS data stream"""
        print("\n📊 Getting NMEA GPS data...")
        
        response = self.send_at('AT+CGPSOUT=1', timeout=3)  # Enable NMEA output
        print(f"NMEA Enable: {response}")
        
        # Read some NMEA sentences
        for i in range(10):
            response = self.send_at('AT+CGPSINFO', timeout=2, expect_ok=False)
            if response:
                print(f"NMEA {i+1}: {response}")
            time.sleep(1)
            
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()

def main():
    print("🛰️ SIM7600G-H GPS Configuration Tool")
    print("====================================")
    
    gps = SIM7600GPS()
    
    # Find AT port
    if not gps.find_at_port():
        print("❌ Could not find SIM7600 AT command port!")
        print("Make sure the cellular module is connected and recognized.")
        sys.exit(1)
        
    try:
        # Check current status
        gps.check_gps_status()
        
        # Enable GPS
        if gps.enable_gps():
            print("✅ GPS enabled successfully!")
            
            # Test GPS data
            fix_found = gps.test_gps_data(duration=120)  # Test for 2 minutes
            
            if fix_found:
                print("\n🎉 SUCCESS! GPS is working!")
                print("📝 Next steps:")
                print("1. Update your telemetry script to use ModemManager GPS")
                print("2. Use: sudo mmcli -m 0 --location-get")
                print("3. Or use AT+CGPSINFO commands directly")
            else:
                print("\n⚠️  GPS enabled but no fix yet")
                print("📝 Troubleshooting:")
                print("1. Ensure device has clear view of sky")
                print("2. Wait 5-15 minutes for cold start")
                print("3. Check antenna connections")
        else:
            print("❌ Failed to enable GPS")
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        gps.close()

if __name__ == "__main__":
    main() 