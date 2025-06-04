#!/usr/bin/env python3
"""
Temperature Monitor for Raspberry Pi
Monitors system temperature and provides cooling recommendations
"""

import subprocess
import time
import os
import signal
import sys

def get_temperature():
    """Get current CPU temperature"""
    try:
        result = subprocess.run(['vcgencmd', 'measure_temp'], 
                               capture_output=True, text=True)
        temp_str = result.stdout.strip()
        # Extract temperature value
        temp = float(temp_str.split('=')[1].replace("'C", ""))
        return temp
    except:
        return None

def get_cpu_usage():
    """Get current CPU usage"""
    try:
        result = subprocess.run(['cat', '/proc/loadavg'], 
                               capture_output=True, text=True)
        load_avg = float(result.stdout.split()[0])
        return load_avg
    except:
        return None

def get_top_processes():
    """Get top CPU consuming processes"""
    try:
        result = subprocess.run(['ps', 'aux', '--sort=-pcpu'], 
                               capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        # Return top 5 processes (skip header)
        return lines[1:6]
    except:
        return []

def stop_high_cpu_services():
    """Stop non-critical services to reduce heat"""
    services_to_stop = [
        'camera-stream.service',  # Camera streaming is CPU intensive
        'flask-dashboard.service'  # Keep Node-RED, stop Flask
    ]
    
    print("🔥 HIGH TEMPERATURE DETECTED - Stopping non-critical services:")
    for service in services_to_stop:
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', service], check=True)
            print(f"   ✓ Stopped {service}")
        except:
            print(f"   ✗ Failed to stop {service}")

def restart_critical_services():
    """Restart services when temperature is back to normal"""
    services_to_restart = [
        'camera-stream.service',
        'flask-dashboard.service'
    ]
    
    print("❄️  TEMPERATURE NORMAL - Restarting services:")
    for service in services_to_restart:
        try:
            subprocess.run(['sudo', 'systemctl', 'start', service], check=True)
            print(f"   ✓ Started {service}")
        except:
            print(f"   ✗ Failed to start {service}")

def optimize_telemetry_frequency():
    """Reduce telemetry collection frequency temporarily"""
    print("⚡ Optimizing telemetry collection frequency...")
    # This would require modifying the telemetry script
    # For now, just log the recommendation
    print("   💡 Consider reducing GPS/sensor polling frequency")

def main():
    print("🌡️  Raspberry Pi Temperature Monitor")
    print("   Press Ctrl+C to exit")
    print("-" * 50)
    
    high_temp_threshold = 80.0  # Celsius
    critical_temp_threshold = 85.0
    normal_temp_threshold = 75.0
    
    temp_emergency_mode = False
    
    try:
        while True:
            temp = get_temperature()
            cpu_usage = get_cpu_usage()
            
            if temp is None:
                print("❌ Could not read temperature")
                time.sleep(5)
                continue
            
            # Color coding for temperature
            if temp < 60:
                temp_color = "🟢"
            elif temp < 70:
                temp_color = "🟡"
            elif temp < 80:
                temp_color = "🟠"
            else:
                temp_color = "🔴"
            
            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp} {temp_color} Temp: {temp:.1f}°C | CPU Load: {cpu_usage:.2f}")
            
            # Emergency cooling actions
            if temp >= critical_temp_threshold and not temp_emergency_mode:
                print("🚨 CRITICAL TEMPERATURE - EMERGENCY COOLING!")
                stop_high_cpu_services()
                optimize_telemetry_frequency()
                temp_emergency_mode = True
                
            elif temp >= high_temp_threshold and not temp_emergency_mode:
                print("⚠️  HIGH TEMPERATURE WARNING")
                print("   Consider reducing workload or improving cooling")
                
            elif temp <= normal_temp_threshold and temp_emergency_mode:
                print("✅ Temperature normalized - restoring services")
                restart_critical_services()
                temp_emergency_mode = False
            
            # Show top processes if temperature is high
            if temp >= high_temp_threshold:
                print("   Top CPU processes:")
                processes = get_top_processes()
                for i, process in enumerate(processes[:3]):
                    parts = process.split()
                    if len(parts) > 10:
                        cpu_percent = parts[2]
                        command = ' '.join(parts[10:])[:50]
                        print(f"     {i+1}. {cpu_percent}% - {command}")
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Temperature monitoring stopped")
        if temp_emergency_mode:
            print("🔄 Restoring services before exit...")
            restart_critical_services()

if __name__ == "__main__":
    main() 