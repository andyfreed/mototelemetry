#!/usr/bin/env python3
"""
Real-time GPS monitoring script
"""

import sqlite3
import time
import os
from datetime import datetime, timedelta

def monitor_gps():
    """Monitor GPS status in real-time"""
    print("🛰️ REAL-TIME GPS MONITOR")
    print("=" * 50)
    print("📍 Watching for GPS signal changes...")
    print("💡 Press Ctrl+C to stop monitoring")
    print("🔌 Now unplug/replug your GPS puck!")
    print()
    
    last_gps_status = None
    last_coords = (0, 0)
    
    try:
        while True:
            try:
                # Connect to database
                conn = sqlite3.connect('/home/pi/motorcycle_data/telemetry.db')
                cursor = conn.cursor()
                
                # Get latest GPS data
                cursor.execute("""
                    SELECT latitude, longitude, speed_mph, fix_status, timestamp
                    FROM telemetry_data 
                    WHERE timestamp > datetime('now', '-10 seconds')
                    ORDER BY timestamp DESC LIMIT 1
                """)
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    lat, lon, speed, fix_status, timestamp = result
                    has_gps = lat != 0 or lon != 0
                    current_coords = (lat, lon)
                    
                    # Clear screen for fresh output
                    os.system('clear')
                    
                    print("🛰️ REAL-TIME GPS MONITOR")
                    print("=" * 50)
                    print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
                    print(f"📡 Fix Status: {fix_status}")
                    
                    if has_gps:
                        print("✅ GPS SIGNAL ACTIVE!")
                        print(f"📍 Latitude:  {lat:.6f}")
                        print(f"📍 Longitude: {lon:.6f}")
                        print(f"🚗 Speed: {speed if speed else 0} mph")
                        
                        if last_gps_status != True:
                            print("🎉 GPS SIGNAL ACQUIRED! Check your dashboard!")
                    else:
                        print("❌ No GPS Signal (coordinates: 0,0)")
                        print("📍 Waiting for satellite lock...")
                        
                        if last_gps_status == True:
                            print("⚠️  GPS SIGNAL LOST!")
                    
                    # Show coordinate changes
                    if current_coords != last_coords:
                        print(f"🔄 Coordinates changed from {last_coords} to {current_coords}")
                    
                    last_gps_status = has_gps
                    last_coords = current_coords
                    
                    print()
                    print("📱 Dashboard: http://localhost:1880/ui")
                    print("🗺️  Map: http://localhost:1880/worldmap")
                    print("💡 Press Ctrl+C to stop monitoring")
                
                else:
                    print("⚠️  No recent telemetry data")
                
            except sqlite3.OperationalError:
                print("⚠️  Database busy, retrying...")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped")
        print("📊 Final GPS status check...")
        
        # Final check
        try:
            conn = sqlite3.connect('/home/pi/motorcycle_data/telemetry.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN latitude != 0 OR longitude != 0 THEN 1 END) as gps_records
                FROM telemetry_data 
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            total, gps_records = cursor.fetchone()
            conn.close()
            
            print(f"📈 Records in last hour: {total}")
            print(f"🛰️ GPS records: {gps_records}")
            print(f"📱 Dashboard: http://localhost:1880/ui")
            
        except Exception as e:
            print(f"Error in final check: {e}")

if __name__ == "__main__":
    monitor_gps() 