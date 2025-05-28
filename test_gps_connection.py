#!/usr/bin/env python3
"""Test GPS connection with gps3 library"""

try:
    from gps3 import gps3
    import time
    
    print("Connecting to GPS...")
    gps_socket = gps3.GPSDSocket()
    gps_socket.connect()
    gps_socket.watch()
    data_stream = gps3.DataStream()
    
    print("GPS connected! Reading data...")
    
    for i in range(20):
        new_data = gps_socket.next()
        if new_data:
            data_stream.unpack(new_data)
            
            if hasattr(data_stream, 'TPV'):
                tpv = data_stream.TPV
                if isinstance(tpv, dict) and 'lat' in tpv and 'lon' in tpv:
                    if tpv['lat'] != 'n/a' and tpv['lon'] != 'n/a':
                        print(f"✅ GPS FIX: Lat={tpv['lat']}, Lon={tpv['lon']}, Speed={tpv.get('speed', 'n/a')}")
                    else:
                        print(f"❌ No GPS fix yet... Mode={tpv.get('mode', 'n/a')}")
                else:
                    print(f"GPS data: {tpv}")
        
        time.sleep(0.5)
        
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying to start gpsd...")
    import subprocess
    subprocess.run(['sudo', 'systemctl', 'start', 'gpsd'])
    print("Please run this script again.") 