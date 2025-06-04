#!/usr/bin/env python3
"""
Immediate Cooling Script for Overheating Raspberry Pi
Reduces CPU load by optimizing running services
"""

import subprocess
import time
import os

def get_temperature():
    """Get current CPU temperature"""
    try:
        result = subprocess.run(['vcgencmd', 'measure_temp'], 
                               capture_output=True, text=True)
        temp_str = result.stdout.strip()
        temp = float(temp_str.split('=')[1].replace("'C", ""))
        return temp
    except:
        return None

def stop_non_essential_services():
    """Stop CPU-intensive but non-critical services"""
    services = [
        'camera-stream.service',  # Camera streaming
        'flask-dashboard.service'  # Flask dashboard (keep Node-RED)
    ]
    
    print("🛑 Stopping non-essential services to reduce heat...")
    for service in services:
        try:
            result = subprocess.run(['sudo', 'systemctl', 'stop', service], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✓ Stopped {service}")
            else:
                print(f"   ⚠️  {service} was not running")
        except Exception as e:
            print(f"   ✗ Failed to stop {service}: {e}")

def reduce_telemetry_frequency():
    """Temporarily reduce telemetry collection frequency"""
    print("⚡ Reducing telemetry collection frequency...")
    
    # Check if we can modify the telemetry script temporarily
    telemetry_file = "/home/pi/motorcycle_telemetry.py"
    if os.path.exists(telemetry_file):
        print("   💡 Telemetry script found - consider manually reducing polling rate")
        print("   💡 Current script is likely polling sensors too frequently")
    
    # Restart telemetry with lower priority
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'motorcycle-telemetry.service'])
        print("   ✓ Restarted telemetry service (may help)")
    except:
        print("   ⚠️  Could not restart telemetry service")

def optimize_cpu_governor():
    """Set CPU governor to powersave mode"""
    print("🔋 Setting CPU to power-save mode...")
    try:
        # Check current governor
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r') as f:
            current_governor = f.read().strip()
        print(f"   Current governor: {current_governor}")
        
        # Set to powersave if not already
        if current_governor != 'powersave':
            subprocess.run(['sudo', 'sh', '-c', 
                           'echo powersave > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'])
            print("   ✓ CPU governor set to powersave")
        else:
            print("   ✓ CPU already in powersave mode")
    except Exception as e:
        print(f"   ✗ Could not change CPU governor: {e}")

def check_cooling_hardware():
    """Check if cooling hardware is working"""
    print("🌪️  Checking cooling hardware...")
    
    # Check for fan control
    fan_paths = [
        '/sys/class/thermal/cooling_device0/cur_state',
        '/sys/class/hwmon/hwmon0/pwm1',
        '/sys/class/hwmon/hwmon1/pwm1'
    ]
    
    fan_found = False
    for fan_path in fan_paths:
        if os.path.exists(fan_path):
            try:
                with open(fan_path, 'r') as f:
                    fan_state = f.read().strip()
                print(f"   ✓ Fan control found: {fan_path} = {fan_state}")
                fan_found = True
            except:
                pass
    
    if not fan_found:
        print("   ⚠️  No active cooling detected - consider adding a fan/heatsink")

def show_immediate_recommendations():
    """Show immediate cooling recommendations"""
    print("\n🧊 IMMEDIATE COOLING RECOMMENDATIONS:")
    print("   1. Add active cooling (fan + heatsink)")
    print("   2. Reduce telemetry polling frequency")
    print("   3. Use only one dashboard (Node-RED OR Flask, not both)")
    print("   4. Move CPU-intensive tasks to external server")
    print("   5. Check for adequate ventilation")
    print("   6. Consider thermal throttling limits")

def main():
    print("🔥 EMERGENCY COOLING - Raspberry Pi Overheating")
    print("=" * 50)
    
    # Get initial temperature
    temp = get_temperature()
    if temp:
        print(f"🌡️  Current temperature: {temp:.1f}°C")
        if temp > 85:
            print("   🚨 CRITICAL - Risk of thermal throttling!")
        elif temp > 80:
            print("   ⚠️  HIGH - Immediate action needed")
    
    print()
    
    # Apply cooling measures
    stop_non_essential_services()
    print()
    
    reduce_telemetry_frequency()
    print()
    
    optimize_cpu_governor()
    print()
    
    check_cooling_hardware()
    print()
    
    show_immediate_recommendations()
    print()
    
    # Check temperature after changes
    print("⏳ Waiting 30 seconds for changes to take effect...")
    time.sleep(30)
    
    new_temp = get_temperature()
    if new_temp and temp:
        temp_change = new_temp - temp
        print(f"🌡️  Temperature after cooling: {new_temp:.1f}°C")
        if temp_change < 0:
            print(f"   ✓ Improved by {abs(temp_change):.1f}°C")
        else:
            print(f"   ⚠️  Still rising (+{temp_change:.1f}°C)")
            print("   💡 Hardware cooling may be needed")
    
    print("\n✅ Emergency cooling measures applied!")
    print("   Run: python3 temp_monitor.py - for continuous monitoring")

if __name__ == "__main__":
    main() 