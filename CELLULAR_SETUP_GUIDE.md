# Motorcycle Telemetry Cellular Broadcasting Setup

## Overview
Your Waveshare SIM7600G-H cellular modem is connected and has created a network interface (`usb0`) with IP `192.168.225.44`. However, it's not yet connected to the internet due to signal/antenna issues.

## Current Status
- ✅ **Modem Detected**: SIM7600G-H recognized by system
- ✅ **SIM Card Active**: Hologram SIM (ICCID: 89464278206109542563)
- ✅ **Network Interface**: usb0 created with local IP
- ❌ **Internet Connection**: Not yet established (signal strength: 99,99 = no signal)
- ✅ **Data Collection**: Telemetry system collecting data at 4-5Hz with 99.2% GPS success

## Cellular Connection Issues
The modem shows no signal (CSQ: 99,99). This typically means:
1. **Antenna not connected properly** - Check both main and diversity antenna connections
2. **Antenna placement** - Antennas need to be outside the metal enclosure
3. **Network coverage** - Verify Hologram has coverage in your area

## Available Solutions

### 1. Web Dashboard (cellular_web_dashboard.py)
Once cellular is connected, this creates a web dashboard accessible remotely:
```bash
python3 cellular_web_dashboard.py
```
- Serves dashboard on port 8080
- Real-time telemetry display
- GPS tracking map
- Accessible at: http://[your-cellular-ip]:8080

### 2. Data Broadcaster (telemetry_broadcaster.py)
Sends telemetry data to a remote server:
```bash
python3 telemetry_broadcaster.py
```
- Supports HTTP POST or TCP socket transmission
- Batches data for efficient transmission
- Queues data when offline

### 3. Simple Test Server (telemetry_server.py)
For testing, run on a remote server:
```bash
python3 telemetry_broadcaster.py --create-server
python3 telemetry_server.py  # Run on your server
```

## Troubleshooting Cellular Connection

### 1. Check Antenna Connections
- Main antenna (ANT MAIN) - primary connection
- Diversity antenna (ANT DIV) - improves signal
- Both should be connected and outside metal enclosure

### 2. Manual AT Commands
Stop ModemManager and test directly:
```bash
sudo systemctl stop ModemManager
sudo python3 configure_sim7600.py
```

### 3. Using ModemManager
```bash
sudo mmcli -m 0  # Check modem status
sudo mmcli -m 0 --simple-connect="apn=hologram"  # Connect
```

### 4. Using NetworkManager
```bash
nmcli device status  # Check devices
nmcli connection up hologram  # Activate connection
```

## Port Forwarding Options

Since cellular connections typically use carrier-grade NAT, incoming connections are blocked. Options:

### 1. VPN Solution (Recommended)
- Use Tailscale, WireGuard, or OpenVPN
- Creates secure tunnel bypassing NAT
- Access dashboard from anywhere

### 2. Reverse Proxy
- Use ngrok or similar service
- Exposes local port to internet
- Example: `ngrok http 8080`

### 3. Cloud Relay
- Send data to cloud service (AWS IoT, Azure IoT Hub)
- Access via cloud dashboard
- Most reliable for production use

## Quick Start Commands

```bash
# Check modem status
sudo mmcli -m 0

# Check signal strength
sudo mmcli -m 0 --signal-get

# Test internet connectivity
ping -I usb0 8.8.8.8

# Start web dashboard (once connected)
python3 cellular_web_dashboard.py

# Start data broadcaster
python3 telemetry_broadcaster.py
```

## Next Steps

1. **Fix antenna setup** - Ensure proper connection and placement
2. **Verify signal** - Move to area with better coverage if needed
3. **Configure VPN** - For remote access to dashboard
4. **Set up cloud relay** - For production data broadcasting

## Support Resources
- Hologram Dashboard: https://dashboard.hologram.io
- SIM7600 AT Commands: Check manufacturer documentation
- Network coverage: Verify 4G LTE coverage in your area 