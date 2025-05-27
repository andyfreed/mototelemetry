#!/usr/bin/env python3
"""
Direct GPS test to debug data collection issues
"""

import json
import time
from gps3 import gps3

def test_gps_data():
    """Test GPS data collection directly"""
    print("🛰️ TESTING GPS DATA COLLECTION")
    print("=" * 40)
    
    try:
        # Initialize GPS
        gps_socket = gps3.GPSDSocket()
        gps_socket.connect()
        gps_socket.watch()
        data_stream = gps3.DataStream()
        
        print("✅ Connected to GPSD")
        print("📡 Collecting GPS data for 30 seconds...")
        print()
        
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < 30:
            new_data = gps_socket.next()
            if new_data:
                data_stream.unpack(new_data)
                
                # Check for TPV (Time-Position-Velocity) data
                if hasattr(data_stream, 'TPV'):
                    tpv = data_stream.TPV
                    count += 1
                    
                    print(f"📊 GPS Reading #{count}")
                    print(f"   Raw TPV: {tpv}")
                    
                    if 'lat' in tpv and 'lon' in tpv:
                        if tpv['lat'] != 'n/a' and tpv['lon'] != 'n/a':
                            lat = float(tpv['lat'])
                            lon = float(tpv['lon'])
                            mode = tpv.get('mode', 0)
                            speed = tpv.get('speed', 'n/a')
                            
                            print(f"   ✅ Valid coordinates: {lat:.6f}, {lon:.6f}")
                            print(f"   📍 Mode: {mode} (1=no fix, 2=2D, 3=3D)")
                            print(f"   🚀 Speed: {speed} m/s")
                        else:
                            print(f"   ❌ Invalid coordinates: lat={tpv['lat']}, lon={tpv['lon']}")
                    else:
                        print(f"   ⚠️  No lat/lon in data")
                    print()
                    
            time.sleep(0.1)
            
        print(f"🏁 Test completed. Collected {count} GPS readings in 30 seconds.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n💡 If you see valid coordinates above, GPS is working!")
    print("   If not, there may be a GPS signal or configuration issue.")

if __name__ == "__main__":
    test_gps_data() 