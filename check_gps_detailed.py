#!/usr/bin/env python3
"""
Detailed GPS Status Checker for Motorcycle Telemetry
Shows comprehensive GPS status and recent data
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

# Database path
DB_PATH = "/home/pi/motorcycle_data/telemetry.db"

def check_gps_status():
    """Check detailed GPS status from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🏍️ MOTORCYCLE GPS STATUS CHECK")
        print("=" * 50)
        
        # Get latest GPS data
        cursor.execute('''
            SELECT latitude, longitude, speed_mph, gps_fix, timestamp, ax, ay, az
            FROM telemetry_data 
            ORDER BY timestamp DESC 
            LIMIT 10
        ''')
        recent_data = cursor.fetchall()
        
        if not recent_data:
            print("❌ No telemetry data found in database")
            return
        
        latest = recent_data[0]
        lat, lon, speed, gps_fix, timestamp, ax, ay, az = latest
        
        # Parse timestamp
        last_update = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        age_seconds = (datetime.now(timezone.utc) - last_update).total_seconds()
        
        # GPS Status
        print(f"📍 GPS STATUS:")
        if lat and lon and lat != 0 and lon != 0:
            print(f"   ✅ GPS ACTIVE - Position: {lat:.6f}, {lon:.6f}")
            print(f"   🚀 Speed: {speed:.1f} mph")
            print(f"   🔒 Fix Status: {'3D Fix' if gps_fix else 'No Fix'}")
        else:
            print(f"   ❌ GPS NOT AVAILABLE - No position data")
            print(f"   🔍 Fix Status: {'Searching...' if gps_fix else 'No satellites'}")
        
        print(f"   ⏱️  Last Update: {last_update.strftime('%H:%M:%S')} ({age_seconds:.0f}s ago)")
        
        # Data freshness
        print(f"\n📊 DATA STATUS:")
        if age_seconds < 5:
            print(f"   ✅ Data is FRESH (updated {age_seconds:.0f}s ago)")
        elif age_seconds < 30:
            print(f"   ⚠️  Data is STALE (updated {age_seconds:.0f}s ago)")
        else:
            print(f"   ❌ Data is OLD (updated {age_seconds:.0f}s ago)")
        
        # IMU Status (for context)
        print(f"\n🧭 IMU DATA:")
        print(f"   X-Axis: {ax:,.0f} (raw)")
        print(f"   Y-Axis: {ay:,.0f} (raw)")
        print(f"   Z-Axis: {az:,.0f} (raw)")
        
        # Recent GPS history
        print(f"\n📈 RECENT GPS HISTORY (Last 10 readings):")
        gps_count = 0
        for i, data in enumerate(recent_data):
            lat, lon, speed, gps_fix, timestamp, _, _, _ = data
            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%H:%M:%S')
            
            if lat and lon and lat != 0 and lon != 0:
                print(f"   {i+1:2}. {time_str} - ✅ GPS: {lat:.6f}, {lon:.6f} ({speed:.1f} mph)")
                gps_count += 1
            else:
                print(f"   {i+1:2}. {time_str} - ❌ No GPS")
        
        print(f"\n📊 STATISTICS:")
        print(f"   GPS Success Rate: {gps_count}/10 ({gps_count*10}%)")
        
        # Service status
        cursor.execute('SELECT COUNT(*) FROM telemetry_data')
        total_records = cursor.fetchone()[0]
        print(f"   Total Records: {total_records:,}")
        
        # Check if telemetry service is running
        import subprocess
        try:
            result = subprocess.run(['systemctl', 'is-active', 'motorcycle-telemetry'], 
                                  capture_output=True, text=True)
            service_status = result.stdout.strip()
            if service_status == 'active':
                print(f"   🏍️  Telemetry Service: ✅ Running")
            else:
                print(f"   🏍️  Telemetry Service: ❌ {service_status}")
        except:
            print(f"   🏍️  Telemetry Service: ❓ Unknown")
        
        conn.close()
        
        # Dashboard access info
        print(f"\n🌐 DASHBOARD ACCESS:")
        print(f"   Node-RED Dashboard: http://localhost:1880/ui")
        print(f"   Node-RED Editor: http://localhost:1880")
        print(f"   GPS Map: Available in dashboard when GPS is active")
        
    except Exception as e:
        print(f"❌ Error checking GPS status: {e}")

if __name__ == "__main__":
    check_gps_status() 