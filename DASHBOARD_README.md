# 🏍️ Motorcycle Telemetry Dashboard

## Overview
Modern Flask-based dashboard replacing Node-RED for real-time motorcycle telemetry monitoring with GPS tracking, system health monitoring, and remote access capabilities.

## 🚀 Features

### Real-Time Telemetry
- **Lean Angle**: Live motorcycle lean angle monitoring
- **G-Forces**: Acceleration forces in X, Y, Z axes
- **Speed**: Current speed tracking
- **30+ Hz Data Rate**: High-frequency telemetry updates

### GPS Tracking
- **Interactive Map**: OpenStreetMap integration with real-time positioning
- **SIM7600G-H Integration**: Cellular GPS via `/dev/ttyUSB1`
- **Status Monitoring**: GPS fix status, satellite count, data freshness
- **Historical Data**: 1,282,000+ GPS records in database

### System Monitoring
- **Service Health**: Real-time status of all motorcycle services
- **System Stats**: CPU, memory, temperature monitoring
- **Network Status**: WiFi, cellular, Tailscale connectivity
- **Automatic Recovery**: Failed services auto-restart

## 📱 Access Methods

### Local Network
```bash
http://10.0.0.155:3000
```

### Remote Access (Tailscale VPN)
```bash
http://100.119.155.66:3000
```

### SSH Access
```bash
# Local network
ssh pi@10.0.0.155

# Remote via Tailscale
ssh pi@100.119.155.66
```

## 🔧 System Architecture

### Services (Auto-Start Enabled)
- `motorcycle-telemetry.service` - Telemetry data collection
- `motorcycle-dashboard.service` - Flask dashboard (port 3000)
- `gpsd.service` - GPS daemon for SIM7600G-H
- `gps-proxy.service` - GPS data proxy
- `tailscaled.service` - VPN for remote access

### Boot Process
1. System startup
2. `/etc/rc.local` - Clean startup logging
3. Systemd auto-starts all services
4. Health check via cron after 30 seconds
5. Dashboard available within ~60 seconds

## 📊 Technical Specifications

### Hardware
- **Platform**: Raspberry Pi 5
- **Cellular**: SIM7600G-H module (70% LTE signal)
- **Carrier**: Hologram network
- **GPS**: Integrated SIM7600G-H GPS

### Network
- **WiFi**: 10.0.0.155/24
- **Cellular**: 10.202.236.255/23 (NAT'd)
- **Tailscale**: 100.119.155.66
- **Public IP**: 71.233.38.219

### Database
- **Type**: SQLite
- **Location**: `/home/pi/motorcycle_data/telemetry.db`
- **Records**: 1,282,000+ total records
- **GPS Data**: 817,192 GPS fixes

## 🛠️ Installation & Setup

### Prerequisites
```bash
sudo apt update
sudo apt install python3-pip sqlite3 gpsd gpsd-clients
pip3 install flask flask-socketio sqlite3
```

### Service Installation
```bash
# Copy service file
sudo cp motorcycle-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable motorcycle-dashboard
sudo systemctl start motorcycle-dashboard
```

### Auto-Start Configuration
Services are configured for automatic startup via systemd. No manual intervention required after reboot.

## 📋 Monitoring & Logs

### Service Status
```bash
sudo systemctl status motorcycle-dashboard
sudo systemctl status motorcycle-telemetry
```

### Application Logs
```bash
journalctl -u motorcycle-dashboard -f
journalctl -u motorcycle-telemetry -f
```

### Boot Logs
- Boot process: `/home/pi/motorcycle_data/boot.log`
- Health check: `/home/pi/motorcycle_data/boot_check.log`

## 🔄 Migration from Node-RED

### Completed Changes
- ✅ Node-RED completely removed (446 packages uninstalled)
- ✅ Modern Flask dashboard with WebSocket real-time updates
- ✅ GPS configuration updated for SIM7600G-H cellular GPS
- ✅ All boot scripts updated and cleaned
- ✅ Service conflicts resolved
- ✅ Remote access maintained via Tailscale

### Performance Improvements
- **Resource Usage**: Significantly reduced memory footprint
- **Response Time**: Faster UI with native WebSocket updates
- **Security**: Better authentication and access control
- **Reliability**: Fewer dependencies, more stable operation

## 🌐 Remote Access Notes

### Working Access Methods
- ✅ Local WiFi: Direct access on home network
- ✅ Tailscale VPN: Secure remote access from anywhere
- ❌ Cellular hosting: Blocked by carrier NAT/CGNAT

### Tailscale Network
- **triumphpi**: 100.119.155.66 (Pi)
- **MacBook Pro**: 100.115.47.103 (active)
- **MacBook Air**: 100.105.109.23 (offline)

## 🚨 Troubleshooting

### Dashboard Not Loading
```bash
sudo systemctl restart motorcycle-dashboard
sudo systemctl status motorcycle-dashboard
```

### GPS Issues
```bash
sudo systemctl restart gpsd
gpspipe -w -n 5  # Test GPS data
```

### Network Connectivity
```bash
sudo systemctl restart tailscaled
tailscale status
```

## 📈 Future Enhancements

- [ ] Data export/backup functionality
- [ ] Historical route playback
- [ ] Mobile app integration
- [ ] Advanced analytics dashboard
- [ ] Real-time alerts/notifications

---

**Status**: ✅ Production Ready  
**Last Updated**: June 2025  
**Version**: 2.0 (Flask Migration Complete) 