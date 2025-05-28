#!/usr/bin/env python3
"""
Direct AT command configuration for SIM7600G-H
"""

import serial
import time
import sys

class SIM7600Config:
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
        
    def configure_modem(self):
        """Configure modem for cellular data"""
        print("\n🔧 Configuring SIM7600G-H modem...")
        
        # Reset to defaults
        print("Resetting modem configuration...")
        self.send_at('AT&F', 2)
        
        # Enable error reporting
        self.send_at('AT+CMEE=2')
        
        # Check SIM status
        print("\n📱 Checking SIM card...")
        response = self.send_at('AT+CPIN?')
        print(f"SIM Status: {response}")
        
        if 'READY' not in response:
            print("❌ SIM card not ready!")
            return False
            
        # Get IMSI
        response = self.send_at('AT+CIMI')
        print(f"IMSI: {response}")
        
        # Set full functionality
        print("\n🔌 Setting full functionality...")
        response = self.send_at('AT+CFUN=1', 3)
        print(f"CFUN: {response}")
        
        # Configure network mode (automatic)
        print("\n🌐 Configuring network mode...")
        response = self.send_at('AT+CNMP=2', 2)  # Automatic mode
        print(f"Network mode: {response}")
        
        # Set band to all bands
        response = self.send_at('AT+CNBP=0X7FFFFFFFFFFFFFFF,0X00000000003FFFFE,0X0000000000000001', 2)
        print(f"Band configuration: {response}")
        
        # Check signal strength
        print("\n📶 Checking signal strength...")
        response = self.send_at('AT+CSQ')
        print(f"Signal: {response}")
        
        # Manual network selection to force registration
        print("\n🔍 Scanning for networks (this may take 30-60 seconds)...")
        response = self.send_at('AT+COPS=?', 60)
        print(f"Available networks: {response}")
        
        # Set automatic network selection
        print("\n📡 Setting automatic network selection...")
        response = self.send_at('AT+COPS=0', 10)
        print(f"Network selection: {response}")
        
        # Check registration status
        print("\n📱 Checking registration status...")
        for i in range(10):
            response = self.send_at('AT+CREG?')
            print(f"Network registration: {response}")
            
            response = self.send_at('AT+CGREG?')
            print(f"GPRS registration: {response}")
            
            if ',1' in response or ',5' in response:
                print("✅ Registered on network!")
                break
            else:
                print(f"Waiting for registration... ({i+1}/10)")
                time.sleep(5)
        
        # Configure APN
        print("\n🌐 Configuring APN for Hologram...")
        response = self.send_at('AT+CGDCONT=1,"IP","hologram"', 2)
        print(f"APN configuration: {response}")
        
        # Activate PDP context
        print("\n🔗 Activating data connection...")
        response = self.send_at('AT+CGACT=1,1', 10)
        print(f"PDP activation: {response}")
        
        # Get IP address
        response = self.send_at('AT+CGPADDR=1')
        print(f"IP Address: {response}")
        
        # Enable network interface
        print("\n🌐 Enabling network interface...")
        response = self.send_at('AT+NETOPEN', 10)
        print(f"Network interface: {response}")
        
        return True
        
    def close(self):
        if self.ser:
            self.ser.close()

def main():
    print("🚀 SIM7600G-H Direct Configuration")
    print("==================================")
    
    config = SIM7600Config()
    
    # Find AT port
    if not config.find_at_port():
        print("❌ Could not find AT command port!")
        sys.exit(1)
        
    try:
        # Configure modem
        if config.configure_modem():
            print("\n✅ Modem configuration complete!")
            print("\n📡 Next steps:")
            print("1. Check 'ip addr' for new network interface")
            print("2. Test connectivity with 'ping -I usb0 8.8.8.8'")
            print("3. Configure routing if needed")
        else:
            print("\n❌ Modem configuration failed!")
            
    finally:
        config.close()

if __name__ == "__main__":
    main() 