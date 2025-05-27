#!/usr/bin/env python3
"""
GPS Status Checker
Monitor GPS data collection in real-time
"""

import sqlite3
import time
from datetime import datetime

def check_gps_status():
    """Check current GPS data collection status"""
    try:
        conn = sqlite3.connect('motorcycle_data/telemetry.db')
        cursor = conn.cursor()
        
        # Check total GPS records
        cursor.execute('SELECT COUNT(*) FROM telemetry_data WHERE latitude IS NOT NULL')
        gps_count = cursor.fetchone()[0]
        
        # Check recent GPS data
        cursor.execute('''
            SELECT latitude, longitude, speed_mph, gps_fix, timestamp 
            FROM telemetry_data 
            WHERE latitude IS NOT NULL 
            ORDER BY timestamp DESC 
            LIMIT 5
        ''')
        recent_gps = cursor.fetchall()
        
        # Check if telemetry is currently running
        cursor.execute('''
            SELECT COUNT(*) FROM telemetry_data 
            WHERE timestamp > datetime('now', '-1 minute')
        ''')
        recent_data = cursor.fetchone()[0]
        
        print("🛰️ GPS Status Report")
        print("=" * 50)
        print(f"📊 Total GPS records: {gps_count}")
        print(f"🔄 Recent telemetry data: {recent_data} records in last minute")
        
        if gps_count > 0:
            print("\n✅ GPS IS WORKING! Recent coordinates:")
            for i, row in enumerate(recent_gps, 1):
                lat, lon, speed, fix, timestamp = row
                print(f"  {i}. Lat: {lat:.6f}, Lon: {lon:.6f}")
                print(f"     Speed: {speed} mph, Fix: {fix}, Time: {timestamp}")
        else:
            print("\n⏳ No GPS coordinates yet")
            print("   GPS may need more time to get satellite fix")
            print("   This is normal - can take 2-15 minutes outdoors")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking GPS status: {e}")

def monitor_gps_live():
    """Monitor GPS data collection in real-time"""
    print("🛰️ Live GPS Monitor - Press Ctrl+C to stop")
    print("=" * 50)
    
    last_count = 0
    
    try:
        while True:
            conn = sqlite3.connect('motorcycle_data/telemetry.db')
            cursor = conn.cursor()
            
            # Check current GPS count
            cursor.execute('SELECT COUNT(*) FROM telemetry_data WHERE latitude IS NOT NULL')
            current_count = cursor.fetchone()[0]
            
            # Check latest GPS data
            cursor.execute('''
                SELECT latitude, longitude, speed_mph, timestamp 
                FROM telemetry_data 
                WHERE latitude IS NOT NULL 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            latest = cursor.fetchone()
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            if current_count > last_count:
                print(f"🆕 {timestamp} - NEW GPS DATA!")
                if latest:
                    lat, lon, speed, db_time = latest
                    print(f"    📍 Lat: {lat:.6f}, Lon: {lon:.6f}")
                    print(f"    🚀 Speed: {speed} mph")
                    print(f"    ⏰ Time: {db_time}")
                last_count = current_count
            else:
                print(f"⏳ {timestamp} - Waiting for GPS fix... (Total: {current_count} GPS records)")
            
            conn.close()
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n👋 GPS monitoring stopped")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_gps_live()
    else:
        check_gps_status()
        print("\n💡 To monitor GPS live: python3 check_gps_status.py monitor") 