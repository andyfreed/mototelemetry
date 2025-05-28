#!/usr/bin/env python3
"""
Setup script for SIM7600G-H cellular modem
Configures the modem and establishes internet connection
"""

import serial
import time
import subprocess
import sys
import os

class CellularModem:
    def __init__(self, port='/dev/ttyUSB2', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def connect(self):
        """Connect to the modem"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"✅ Connected to modem on {self.port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    def send_at_command(self, command, wait_time=1):
        """Send AT command and get response"""
        if not self.ser:
            return None
            
        # Clear any pending data
        self.ser.flushInput()
        
        # Send command
        self.ser.write((command + '\r\n').encode())
        time.sleep(wait_time)
        
        # Read response
        response = ''
        while self.ser.in_waiting:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
            time.sleep(0.1)
            
        return response.strip()
    
    def check_modem_status(self):
        """Check basic modem status"""
        print("\n🔍 Checking modem status...")
        
        # Test AT command
        response = self.send_at_command('AT')
        if 'OK' in response:
            print("✅ Modem responding to AT commands")
        else:
            print("❌ Modem not responding")
            return False
            
        # Check manufacturer
        response = self.send_at_command('AT+CGMI')
        lines = response.split('\n')
        print(f"📱 Manufacturer: {lines[1] if len(lines) > 1 else 'Unknown'}")
        
        # Check model
        response = self.send_at_command('AT+CGMM')
        lines = response.split('\n')
        print(f"📱 Model: {lines[1] if len(lines) > 1 else 'Unknown'}")
        
        # Check IMEI
        response = self.send_at_command('AT+CGSN')
        lines = response.split('\n')
        print(f"📱 IMEI: {lines[1] if len(lines) > 1 else 'Unknown'}")
        
        return True
    
    def check_sim_status(self):
        """Check SIM card status"""
        print("\n🔍 Checking SIM card...")
        
        # Check SIM status
        response = self.send_at_command('AT+CPIN?')
        if 'READY' in response:
            print("✅ SIM card ready")
        else:
            print(f"❌ SIM status: {response}")
            return False
            
        # Get ICCID
        response = self.send_at_command('AT+CICCID')
        if '+ICCID:' in response:
            iccid = response.split('+ICCID:')[1].split('\n')[0].strip()
            print(f"📱 SIM ICCID: {iccid}")
            
        # Get operator
        response = self.send_at_command('AT+COPS?', wait_time=3)
        print(f"📱 Network operator: {response}")
        
        return True
    
    def check_signal_strength(self):
        """Check signal strength"""
        response = self.send_at_command('AT+CSQ')
        if '+CSQ:' in response:
            rssi = response.split('+CSQ:')[1].split(',')[0].strip()
            rssi_val = int(rssi)
            if rssi_val < 10:
                signal = "Poor"
            elif rssi_val < 15:
                signal = "Fair"
            elif rssi_val < 20:
                signal = "Good"
            else:
                signal = "Excellent"
            print(f"📶 Signal strength: {rssi} ({signal})")
            
    def setup_network(self):
        """Configure network settings"""
        print("\n🌐 Configuring network...")
        
        # Set network mode to automatic
        response = self.send_at_command('AT+CNMP=2', wait_time=2)
        print("✅ Set network mode to automatic")
        
        # Check network registration
        response = self.send_at_command('AT+CREG?')
        if ',1' in response or ',5' in response:
            print("✅ Registered on network")
        else:
            print(f"⏳ Network registration status: {response}")
            
        # Check PS registration (data)
        response = self.send_at_command('AT+CGREG?')
        if ',1' in response or ',5' in response:
            print("✅ Data service registered")
        else:
            print(f"⏳ Data registration status: {response}")
            
    def setup_apn(self, apn="hologram"):
        """Configure APN settings"""
        print(f"\n📡 Configuring APN: {apn}")
        
        # Define PDP context
        response = self.send_at_command(f'AT+CGDCONT=1,"IP","{apn}"', wait_time=2)
        if 'OK' in response:
            print("✅ APN configured")
        else:
            print(f"❌ APN configuration failed: {response}")
            
    def connect_internet(self):
        """Establish internet connection"""
        print("\n🌐 Connecting to internet...")
        
        # Activate PDP context
        response = self.send_at_command('AT+CGACT=1,1', wait_time=5)
        if 'OK' in response:
            print("✅ PDP context activated")
        else:
            print(f"❌ PDP activation failed: {response}")
            return False
            
        # Get IP address
        response = self.send_at_command('AT+CGPADDR=1')
        if '+CGPADDR:' in response:
            ip = response.split('"')[1] if '"' in response else 'Unknown'
            print(f"✅ IP Address: {ip}")
            
        return True
    
    def setup_ppp(self):
        """Setup PPP connection for system-wide internet"""
        print("\n🔧 Setting up PPP connection...")
        
        # Create PPP peer configuration
        ppp_config = """
# SIM7600 PPP configuration
/dev/ttyUSB3
115200
defaultroute
usepeerdns
noauth
persist
debug
"""
        
        # Write PPP peer config
        try:
            with open('/tmp/sim7600_ppp', 'w') as f:
                f.write(ppp_config)
            
            # Create chat script
            chat_script = """
ABORT "NO CARRIER"
ABORT "NO DIALTONE"
ABORT "ERROR"
ABORT "NO ANSWER"
ABORT "BUSY"
TIMEOUT 30
"" AT
OK ATH
OK ATZ
OK AT+CGDCONT=1,"IP","hologram"
OK ATD*99#
CONNECT ""
"""
            
            with open('/tmp/sim7600_chat', 'w') as f:
                f.write(chat_script)
                
            print("✅ PPP configuration created")
            print("\n📝 To start PPP connection, run:")
            print("   sudo pppd file /tmp/sim7600_ppp connect 'chat -v -f /tmp/sim7600_chat'")
            
        except Exception as e:
            print(f"❌ Failed to create PPP config: {e}")
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()

def main():
    print("🚀 SIM7600G-H Cellular Modem Setup")
    print("==================================")
    
    # Check if running with proper permissions
    if os.geteuid() != 0:
        print("⚠️  Note: Some operations may require sudo privileges")
    
    # Initialize modem
    modem = CellularModem()
    
    if not modem.connect():
        sys.exit(1)
    
    try:
        # Check modem status
        if not modem.check_modem_status():
            sys.exit(1)
            
        # Check SIM
        if not modem.check_sim_status():
            sys.exit(1)
            
        # Check signal
        modem.check_signal_strength()
        
        # Setup network
        modem.setup_network()
        
        # Configure APN (using Hologram as default)
        modem.setup_apn("hologram")
        
        # Connect to internet
        modem.connect_internet()
        
        # Setup PPP for system-wide connection
        modem.setup_ppp()
        
        print("\n✅ Cellular modem setup complete!")
        print("\n📡 Next steps:")
        print("1. Start PPP connection for system internet")
        print("2. Or use the modem's built-in TCP/IP stack for direct data transmission")
        
    finally:
        modem.close()

if __name__ == "__main__":
    main() 