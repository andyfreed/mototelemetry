#!/usr/bin/env python3
"""
Complete cellular connection setup for SIM7600G-H
This script handles the full connection process including interface configuration
"""

import serial
import time
import subprocess
import sys
import os

class SIM7600Cellular:
    def __init__(self):
        self.port = None
        self.ser = None
        
    def find_at_port(self):
        """Find the correct AT command port"""
        ports = ['/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB1', '/dev/ttyUSB0']
        
        for port in ports:
            try:
                print(f"Testing {port}...")
                ser = serial.Serial(port, 115200, timeout=2)
                time.sleep(0.5)
                
                # Clear buffer
                ser.flushInput()
                ser.flushOutput()
                
                # Send AT
                ser.write(b'AT\r\n')
                time.sleep(0.5)
                response = ser.read(100).decode('utf-8', errors='ignore')
                
                if 'OK' in response:
                    print(f"✅ Found AT port: {port}")
                    self.port = port
                    self.ser = ser
                    return True
                    
                ser.close()
            except Exception as e:
                print(f"Error on {port}: {e}")
                
        return False
        
    def send_at(self, command, wait=1):
        """Send AT command and return response"""
        if not self.ser:
            return None
            
        self.ser.flushInput()
        self.ser.write(f'{command}\r\n'.encode())
        time.sleep(wait)
        
        response = ''
        while self.ser.in_waiting:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
            
        return response.strip()
        
    def setup_cellular_connection(self):
        """Complete cellular connection setup"""
        print("\n🚀 Setting up SIM7600G-H cellular connection...")
        
        # Basic modem setup
        print("📱 Configuring modem...")
        self.send_at('AT+CFUN=1', 3)  # Full functionality
        self.send_at('AT+CNMP=2')     # Automatic network mode
        
        # Check registration
        print("📡 Checking network registration...")
        for i in range(10):
            response = self.send_at('AT+CREG?')
            if ',1' in response or ',5' in response:
                print("✅ Registered on network!")
                break
            print(f"Waiting for registration... ({i+1}/10)")
            time.sleep(3)
        
        # Configure APN and activate connection
        print("🌐 Setting up data connection...")
        self.send_at('AT+CGDCONT=1,"IP","hologram"', 2)
        self.send_at('AT+CGACT=1,1', 5)
        
        # Get IP configuration
        response = self.send_at('AT+CGPADDR=1')
        ip_address = None
        if '+CGPADDR:' in response:
            try:
                # Parse IP from response like: +CGPADDR: 1,"10.202.236.255"
                lines = response.split('\n')
                for line in lines:
                    if '+CGPADDR:' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            ip_address = parts[1].strip().strip('"').strip()
                            # Remove any extra whitespace or control characters
                            ip_address = ''.join(c for c in ip_address if c.isprintable() and not c.isspace())
                            break
                
                if ip_address and '.' in ip_address:
                    print(f"📱 Assigned IP: {ip_address}")
                else:
                    print("❌ Could not parse valid IP address")
                    return False
            except Exception as e:
                print(f"❌ Could not parse IP address: {e}")
                return False
        
        # Enable network interface
        self.send_at('AT+NETOPEN', 5)
        
        return ip_address
        
    def configure_system_interface(self, ip_address):
        """Configure system network interface"""
        print("\n🔧 Configuring system interface...")
        
        try:
            # Bring up interface
            subprocess.run(['sudo', 'ip', 'link', 'set', 'wwan0', 'up'], check=True)
            print("✅ Interface brought up")
            
            # Remove any existing IP
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', 'wwan0'], check=False)
            
            # Add IP address
            subprocess.run(['sudo', 'ip', 'addr', 'add', f'{ip_address}/23', 'dev', 'wwan0'], check=True)
            print(f"✅ IP address {ip_address} assigned")
            
            # Add default route with lower priority than WiFi
            subprocess.run(['sudo', 'ip', 'route', 'add', 'default', 'dev', 'wwan0', 'metric', '800'], check=False)
            print("✅ Default route added")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Interface configuration failed: {e}")
            return False
            
    def test_connectivity(self):
        """Test cellular internet connectivity"""
        print("\n🌐 Testing connectivity...")
        
        try:
            result = subprocess.run(['ping', '-I', 'wwan0', '-c', '3', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("✅ Cellular internet connection working!")
                return True
            else:
                print("❌ Ping test failed")
                print(result.stdout)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Ping test timed out")
            return False
            
    def create_connection_service(self):
        """Create systemd service for automatic connection"""
        service_content = """[Unit]
Description=SIM7600G-H Cellular Connection
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/pi/setup_cellular_connection.py --connect-only
RemainAfterExit=yes
User=root

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open('/tmp/cellular-connection.service', 'w') as f:
                f.write(service_content)
            
            subprocess.run(['sudo', 'cp', '/tmp/cellular-connection.service', 
                          '/etc/systemd/system/'], check=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'cellular-connection.service'], check=True)
            
            print("✅ Cellular connection service created and enabled")
            return True
            
        except Exception as e:
            print(f"❌ Service creation failed: {e}")
            return False
            
    def close(self):
        if self.ser:
            self.ser.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='SIM7600G-H Cellular Setup')
    parser.add_argument('--connect-only', action='store_true', 
                       help='Only establish connection (for service)')
    args = parser.parse_args()
    
    print("🚀 SIM7600G-H Cellular Connection Setup")
    print("=====================================")
    
    # Stop ModemManager temporarily
    if not args.connect_only:
        print("🔧 Stopping ModemManager temporarily...")
        subprocess.run(['sudo', 'systemctl', 'stop', 'ModemManager'], check=False)
        time.sleep(2)
    
    cellular = SIM7600Cellular()
    
    try:
        # Find AT port
        if not cellular.find_at_port():
            print("❌ Could not find AT command port!")
            return 1
            
        # Setup cellular connection
        ip_address = cellular.setup_cellular_connection()
        if not ip_address:
            print("❌ Failed to establish cellular connection!")
            return 1
            
        # Configure system interface
        if not cellular.configure_system_interface(ip_address):
            print("❌ Failed to configure system interface!")
            return 1
            
        # Test connectivity
        if cellular.test_connectivity():
            print("\n🎉 Cellular connection setup complete!")
            
            if not args.connect_only:
                # Create service for automatic connection
                cellular.create_connection_service()
                
                print("\n📋 Connection Summary:")
                print(f"   📱 Modem: SIM7600G-H")
                print(f"   🌐 Network: Hologram")
                print(f"   📍 IP Address: {ip_address}")
                print(f"   🔗 Interface: wwan0")
                print("\n🚀 Your motorcycle telemetry system now has cellular connectivity!")
                print("   You can now use cellular_web_dashboard.py or telemetry_broadcaster.py")
                
        else:
            print("❌ Connectivity test failed!")
            return 1
            
    finally:
        cellular.close()
        
        if not args.connect_only:
            # Restart ModemManager
            print("\n🔧 Restarting ModemManager...")
            subprocess.run(['sudo', 'systemctl', 'start', 'ModemManager'], check=False)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 