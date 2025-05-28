# 🏍️ Motorcycle Telemetry System

A real-time motorcycle telemetry data collection and visualization system using Raspberry Pi, IMU sensors, GPS tracking, and Node-RED dashboard.

![Motorcycle Dashboard](https://img.shields.io/badge/Status-Active-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi-red)
![Language](https://img.shields.io/badge/Language-Python-blue)
![Dashboard](https://img.shields.io/badge/Dashboard-Node--RED-orange)

## 🌟 Features

- **Real-time Telemetry**: Live collection of motorcycle sensor data
- **IMU Data**: 3-axis accelerometer for G-force and lean angle calculations
- **GPS Tracking**: Real-time location tracking with interactive map
- **Live Dashboard**: Web-based dashboard with gauges and visualizations
- **Data Storage**: SQLite database for historical data analysis
- **Mobile Responsive**: Dashboard works on phones and tablets

## 📊 Dashboard Metrics

- **🏍️ Lean Angle**: ±60° range with color-coded safety zones
- **⚡ Forward G-Force**: ±1.5g acceleration/braking forces
- **🌀 Lateral G-Force**: ±1.2g cornering forces
- **🚀 Speed**: Real-time speed in mph
- **🗺️ GPS Map**: Interactive location tracking
- **🛰️ GPS Status**: Live/Recent/Searching status indicators

## 🛠️ Hardware Requirements

- Raspberry Pi (tested on Pi 4)
- IMU sensor (MPU6050 or similar I2C accelerometer)
- GPS module (U-Blox or compatible USB GPS)
- MicroSD card (16GB+ recommended)
- Power supply for motorcycle mounting

## ⚙️ Software Components

- **Python 3.x**: Core telemetry collection
- **SQLite**: Local data storage
- **Node-RED**: Dashboard and visualization
- **GPSD**: GPS daemon for location services
- **gps3**: Python GPS library

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/andyfreed/mototelemetry.git
cd mototelemetry
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv telemetry-env
source telemetry-env/bin/activate

# Install Python packages
pip install gps3 sqlite3

# Install Node-RED
sudo npm install -g node-red
sudo npm install -g node-red-dashboard
sudo npm install -g node-red-contrib-web-worldmap
```

### 3. Configure GPS
```bash
# Install GPS daemon
sudo apt-get install gpsd gpsd-clients

# Configure for your GPS device (adjust /dev/ttyACM1 as needed)
sudo gpsd -n /dev/ttyACM1
```

### 4. Start Services
```bash
# Start telemetry collection
python3 motorcycle_telemetry.py &

# Start Node-RED dashboard
node-red &

# Deploy dashboard
python3 deploy_final_dashboard.py
```

### 5. Access Dashboard
- **Main Dashboard**: http://localhost:1880/ui
- **GPS Map**: http://localhost:1880/worldmap
- **Node-RED Editor**: http://localhost:1880

## 📁 Project Structure

```
mototelemetry/
├── motorcycle_telemetry.py     # Main telemetry collection script
├── deploy_final_dashboard.py   # Dashboard deployment script
├── calibrated_dashboard.py     # Sensor calibration utilities
├── test_gps_direct.py         # GPS testing and debugging
├── setup_telemetry.sh         # System setup script
├── fix_network.sh             # Network configuration fix
├── motorcycle_data/           # Data directory
│   └── telemetry.db          # SQLite database
├── node_red_flows/           # Node-RED flow configurations
├── docs/                     # Documentation
└── README.md                 # This file
```

## 🔧 Configuration

### IMU Calibration
The system includes calibration constants for accurate G-force calculations:
```python
X_OFFSET = 6200    # X-axis offset
Y_OFFSET = 100     # Y-axis offset  
Z_OFFSET = 15400   # Z-axis offset
SCALE = 16384      # Scale factor for ±2g range
```

### GPS Setup
Ensure your GPS device is properly configured:
```bash
# Check GPS device
lsusb | grep -i gps

# Test GPS connection
python3 test_gps_direct.py
```

## 📈 Data Schema

### SQLite Database Structure
```sql
CREATE TABLE telemetry_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ax REAL,           -- X-axis acceleration
    ay REAL,           -- Y-axis acceleration  
    az REAL,           -- Z-axis acceleration
    latitude REAL,     -- GPS latitude
    longitude REAL,    -- GPS longitude
    speed_mph REAL,    -- Speed in mph
    fix_status INTEGER -- GPS fix status
);
```

## 🗺️ GPS Features

- **Live Tracking**: Real-time motorcycle position
- **Status Indicators**: 
  - ✅ GPS Active (live coordinates)
  - 🟡 GPS Recent (cached within 30s)
  - 🔍 GPS Searching (fallback location)
- **Multiple Map Options**: Node-RED worldmap + Google Maps fallback

## 🎯 Calibration Process

1. **Static Calibration**: Record sensor readings while stationary
2. **Offset Calculation**: Determine X, Y, Z axis offsets
3. **Scale Verification**: Confirm ±2g range accuracy
4. **Lean Angle Validation**: Test with known lean angles

## 🔄 System Architecture

```
IMU Sensor ──┐
              ├── motorcycle_telemetry.py ──► SQLite DB ──► Node-RED ──► Dashboard
GPS Module ──┘                                                      └── Worldmap
```

## 🚧 Troubleshooting

### Common Issues

**GPS Not Working:**
```bash
# Check GPS device
sudo dmesg | grep tty
sudo gpsd -n /dev/ttyACM1  # Adjust device path
```

**Dashboard Not Loading:**
```bash
# Check Node-RED status
ps aux | grep node-red
# Restart if needed
pkill node-red && node-red &
```

**Database Locked:**
```bash
# Check for running processes
ps aux | grep telemetry
# Kill if necessary and restart
```

**Map Not Loading:**
```bash
# Fix network routing
./fix_network.sh
```

## 📱 Mobile Access

The dashboard is fully responsive and works on mobile devices. Access via:
- Phone browser: `http://[pi-ip-address]:1880/ui`
- Tablet: Optimized layout for larger screens
- Desktop: Full feature access

## 🛡️ Safety Considerations

- **Secure Mounting**: Ensure Raspberry Pi is safely mounted
- **Power Management**: Use proper motorcycle power supply
- **Weather Protection**: Protect electronics from elements
- **Distraction-Free**: Dashboard designed for passenger/pit crew use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Raspberry Pi Foundation for the amazing hardware platform
- Node-RED community for the excellent dashboard framework
- OpenStreetMap for map tile services
- GPS and IMU sensor manufacturers

## 📞 Support

For support, open an issue on GitHub or contact the maintainers.

## 🔮 Future Enhancements

- [ ] Bluetooth Low Energy (BLE) connectivity
- [ ] Advanced analytics and ride reports
- [ ] Integration with motorcycle CAN bus
- [ ] Machine learning for riding pattern analysis
- [ ] Cloud data synchronization
- [ ] Mobile app companion

## GPS Troubleshooting

If you're experiencing issues with GPS on your motorcycle telemetry system, there are several tools to help diagnose and fix common problems:

### Quick GPS Fix

Run the GPS fix script to automatically detect and fix common GPS issues:

```bash
sudo ./fix_gps.sh
```

This script will:
1. Detect your GPS device and correct serial port
2. Configure and restart the GPS daemon (gpsd)
3. Restart the telemetry service
4. Update Node-RED with the correct camera URL

### Comprehensive GPS Debugging

For a more detailed analysis of GPS issues, run the debugging script:

```bash
python3 debug_gps.py
```

This script performs a complete diagnostic of your GPS system:
- Checks GPS hardware connection
- Verifies the GPS daemon is running
- Examines GPS data in the database
- Tests direct GPS access
- Provides suggestions for fixing any detected issues

### Manual GPS Fix Steps

If the automated scripts don't resolve your issue:

1. Ensure the GPS device is properly connected (should appear as U-Blox device in `lsusb`)
2. Verify the GPS is accessible at `/dev/ttyACM0` or similar
3. Check the GPS daemon status: `systemctl status gpsd`
4. If needed, manually start GPS: `sudo gpsd -n /dev/ttyACM0`
5. Restart telemetry: `sudo systemctl restart motorcycle-telemetry`
6. Check GPS data: `gpspipe -w`

Remember that GPS typically requires a clear view of the sky and may take 2-5 minutes to acquire a satellite fix when starting from a cold state.

---

**⚠️ Disclaimer**: This system is designed for data collection and analysis purposes. Always prioritize safety while riding. Do not interact with the dashboard while operating the motorcycle. 