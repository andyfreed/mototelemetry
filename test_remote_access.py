#!/usr/bin/env python3
"""
Remote Access Diagnostic Tool
Tests all components needed for remote motorcycle dashboard access
"""

import subprocess
import requests
import sqlite3
import json
from datetime import datetime, timedelta

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode == 0
    except Exception as e:
        return str(e), False

def test_service_status():
    """Test all required services"""
    print("🔧 SERVICE STATUS:")
    print("=" * 40)
    
    services = {
        "🏍️ Telemetry": "motorcycle-telemetry",
        "📊 Node-RED": "nodered", 
        "📹 Camera": "camera-stream",
        "🛰️ GPS": "gpsd-custom",
        "🛰️ GPS Proxy": "gps-proxy",
        "🗺️ Route Tracker": "route-tracker",
        "🔒 Tailscale": "tailscaled",
        "📡 Cellular": "ModemManager"
    }
    
    for name, service in services.items():
        status, success = run_command(f"systemctl is-active {service}")
        icon = "✅" if status == "active" else "❌"
        print(f"{icon} {name}: {status}")
    
    print()

def test_network_access():
    """Test network connectivity"""
    print("🌐 NETWORK ACCESS:")
    print("=" * 40)
    
    # Get Tailscale IP
    tailscale_ip, _ = run_command("tailscale ip -4")
    print(f"📱 Tailscale IP: {tailscale_ip}")
    
    # Test local services
    tests = [
        ("📊 Node-RED Dashboard", f"http://127.0.0.1:1880/ui"),
        ("🔧 Node-RED Editor", f"http://127.0.0.1:1880"),
        ("📹 Camera Stream", f"http://127.0.0.1:8090"),
        ("🛰️ GPS Proxy", f"http://127.0.0.1:2948"),
        ("🗺️ Route Tracker", f"http://127.0.0.1:5001/api/tracking_status")
    ]
    
    for name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            icon = "✅" if response.status_code < 400 else "⚠️"
            print(f"{icon} {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
    
    print()

def test_gps_data():
    """Test GPS data availability"""
    print("🛰️ GPS DATA:")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('/home/pi/motorcycle_data/telemetry.db')
        cursor = conn.cursor()
        
        # Check recent data
        cursor.execute('''
            SELECT COUNT(*) FROM telemetry_data 
            WHERE timestamp > datetime("now", "-5 minutes")
        ''')
        recent_count = cursor.fetchone()[0]
        
        # Get latest GPS data
        cursor.execute('''
            SELECT latitude, longitude, speed_mph, gps_fix, timestamp 
            FROM telemetry_data 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        latest = cursor.fetchone()
        
        if latest:
            lat, lon, speed, fix, timestamp = latest
            has_coordinates = lat != 0 and lon != 0
            has_fix = bool(fix)
            
            print(f"📊 Recent records (5 min): {recent_count}")
            print(f"📍 Latest coordinates: {lat:.6f}, {lon:.6f}")
            print(f"🚗 Speed: {speed:.1f} mph")
            print(f"🛰️ GPS Fix: {'Yes' if has_fix else 'No'}")
            print(f"⏰ Last update: {timestamp}")
            
            if has_coordinates and has_fix:
                print("✅ GPS Status: ACTIVE with valid coordinates")
            elif has_fix:
                print("⚠️ GPS Status: Fix acquired but invalid coordinates")
            else:
                print("❌ GPS Status: Searching for satellites")
        else:
            print("❌ No GPS data found")
            
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print()

def test_remote_urls():
    """Show remote access URLs"""
    print("🌐 REMOTE ACCESS URLS:")
    print("=" * 40)
    
    tailscale_ip, _ = run_command("tailscale ip -4")
    
    if tailscale_ip:
        urls = [
            ("📊 Dashboard", f"http://{tailscale_ip}:1880/ui"),
            ("🔧 Node-RED Editor", f"http://{tailscale_ip}:1880"),
            ("📹 Camera Feed", f"http://{tailscale_ip}:8090"),
            ("🛰️ GPS Proxy", f"telnet {tailscale_ip} 2948"),
            ("🗺️ Route API", f"http://{tailscale_ip}:5001/api/tracking_status")
        ]
        
        for name, url in urls:
            print(f"{name}: {url}")
    else:
        print("❌ Tailscale IP not available")
    
    print()

def main():
    """Run all diagnostic tests"""
    print("🏍️ MOTORCYCLE DASHBOARD REMOTE ACCESS DIAGNOSTIC")
    print("=" * 60)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_service_status()
    test_network_access() 
    test_gps_data()
    test_remote_urls()
    
    print("🔍 TROUBLESHOOTING TIPS:")
    print("=" * 40)
    print("• If 'GPS NOT AVAILABLE' shows remotely but GPS data exists:")
    print("  - Camera feed may be failing (check camera service)")
    print("  - Route tracker API may be unreachable")
    print("  - Browser cache issues (try hard refresh: Ctrl+F5)")
    print("")
    print("• For camera issues:")
    print("  - Check: systemctl status camera-stream")
    print("  - Restart: sudo systemctl restart camera-stream")
    print("")
    print("• For GPS issues:")
    print("  - Check: python3 check_gps_status.py")
    print("  - Restart: sudo systemctl restart gpsd-custom")
    print("")
    print("✅ Test complete!")

if __name__ == "__main__":
    main() 