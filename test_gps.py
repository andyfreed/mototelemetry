#!/usr/bin/env python3
"""
GPS Test Script
Check if GPS is working and collecting coordinates
"""

import time
import sys

def test_gps_gpsd():
    """Test GPS using gpsd library"""
    try:
        import gps
        print("📡 Testing GPS with gpsd library...")
        
        # Connect to GPS daemon
        session = gps.gps("localhost", "2947")
        session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
        
        print("🔄 Waiting for GPS fix... (this may take 30-60 seconds)")
        
        for i in range(30):  # Try for 30 seconds
            try:
                report = session.next()
                print(f"📦 GPS Report: {report}")
                
                if report['class'] == 'TPV':
                    lat = getattr(report, 'lat', None)
                    lon = getattr(report, 'lon', None)
                    speed = getattr(report, 'speed', None)
                    mode = getattr(report, 'mode', 0)
                    
                    print(f"🛰️  GPS Status:")
                    print(f"   Mode: {mode} (1=no fix, 2=2D, 3=3D)")
                    print(f"   Latitude: {lat}")
                    print(f"   Longitude: {lon}")
                    print(f"   Speed: {speed} m/s")
                    
                    if lat is not None and lon is not None:
                        print("✅ GPS is working! Getting coordinates.")
                        return True
                        
            except Exception as e:
                print(f"   Attempt {i+1}: {e}")
                time.sleep(2)
                
        print("❌ No GPS fix obtained")
        return False
        
    except ImportError:
        print("❌ gps library not installed")
        return False
    except Exception as e:
        print(f"❌ GPS error: {e}")
        return False

def test_gps_serial():
    """Test GPS by reading raw NMEA data from serial port"""
    try:
        import serial
        print("\n📡 Testing GPS via serial port...")
        
        # Try common GPS ports
        ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0']
        
        for port in ports:
            try:
                print(f"🔌 Trying port: {port}")
                ser = serial.Serial(port, 9600, timeout=5)
                
                for i in range(10):
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    print(f"   {line}")
                    
                    if line.startswith('$GPGGA') or line.startswith('$GPRMC'):
                        print(f"✅ Found GPS NMEA data on {port}")
                        ser.close()
                        return True
                        
                ser.close()
                
            except Exception as e:
                print(f"   Error on {port}: {e}")
                
        print("❌ No GPS NMEA data found")
        return False
        
    except ImportError:
        print("❌ pyserial library not installed")
        return False

def main():
    print("🏍️ GPS Test for Motorcycle Telemetry")
    print("=" * 50)
    
    # Test GPS daemon first
    gps_working = test_gps_gpsd()
    
    if not gps_working:
        # Try direct serial access
        print("\n🔄 Trying direct serial access...")
        gps_working = test_gps_serial()
    
    print("\n" + "=" * 50)
    if gps_working:
        print("✅ GPS is working! You can now:")
        print("   🗺️  Create map visualizations in Grafana")
        print("   📍 Track your motorcycle routes")
        print("   🚀 Monitor GPS speed")
        print("   🧭 Track heading/direction")
    else:
        print("❌ GPS not working. Check:")
        print("   📡 GPS module is connected")
        print("   🔌 Correct USB/UART port")
        print("   📶 GPS has clear sky view")
        print("   ⏰ Wait longer for GPS fix (can take minutes)")
        
    print(f"\n🔧 To fix GPS in telemetry system:")
    print(f"   1. Ensure GPS is working with this test")
    print(f"   2. Update telemetry system with correct GPS setup")
    print(f"   3. Restart telemetry service")

if __name__ == "__main__":
    main() 