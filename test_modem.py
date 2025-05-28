#!/usr/bin/env python3
import serial
import time

ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4']

for port in ports:
    print(f"\nTesting {port}...")
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(0.5)
        
        # Send AT command
        ser.write(b'AT\r\n')
        time.sleep(0.5)
        
        # Read response
        response = ser.read(100).decode('utf-8', errors='ignore')
        
        if response:
            print(f"✅ Response from {port}:")
            print(response)
            
            # Try to get more info
            ser.write(b'AT+CGMI\r\n')
            time.sleep(0.5)
            response = ser.read(100).decode('utf-8', errors='ignore')
            if response:
                print(f"Manufacturer info: {response}")
        else:
            print(f"❌ No response from {port}")
            
        ser.close()
        
    except Exception as e:
        print(f"❌ Error on {port}: {e}") 