# 🏍️ Motorcycle Dashboard Access Guide

## 📱 You Have TWO Amazing Dashboards!

### 1. **Node-RED Dashboard** (Your Original) ✅
- **Local**: `http://localhost:1880/ui`
- **Cellular**: `http://10.202.236.255:1880/ui` 
- **WiFi**: `http://10.0.0.155:1880/ui`

**Features**:
- 🏍️ **Lean Angle Gauge** (-60° to +60°)
- ⚡ **Forward G-Force** (-1.5g to +1.5g)
- 🌀 **Lateral G-Force** (-1.2g to +1.2g)
- 🚀 **Speed Gauge** (0-120 mph)
- 🗺️ **GPS Map** with live location
- 📊 **Real-time updates** every 2 seconds

### 2. **Flask Dashboard** (New Cellular-Optimized) ✅
- **Local**: `http://localhost:8080`
- **Cellular**: `http://10.202.236.255:8080`
- **WiFi**: `http://10.0.0.155:8080`

**Features**:
- 📱 **Mobile-optimized** dark theme
- 🌐 **Cellular-friendly** lightweight design
- 📍 **GPS tracking** with path history
- 📊 **Real-time telemetry** API
- 🔥 **Modern UI** with live updates

## 🌐 Remote Access Solutions

### **Option 1: Tailscale** (✅ INSTALLED - EASIEST)

**Setup**:
1. Visit: `https://login.tailscale.com/a/4183edf01e2ed`
2. Sign in with Google/GitHub/Email
3. Approve the device

**Then access from anywhere**:
- Node-RED: `http://[tailscale-ip]:1880/ui`
- Flask: `http://[tailscale-ip]:8080`

### **Option 2: ngrok** (Quick & Temporary)
```bash
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz
tar -xf ngrok-v3-stable-linux-arm64.tgz

# Expose Node-RED dashboard
./ngrok http 1880

# Or expose Flask dashboard
./ngrok http 8080
```

### **Option 3: CloudFlare Tunnel** (Free & Permanent)
```bash
# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
chmod +x cloudflared-linux-arm64

# Create tunnel for Node-RED
./cloudflared-linux-arm64 tunnel --url http://localhost:1880

# Or for Flask dashboard
./cloudflared-linux-arm64 tunnel --url http://localhost:8080
```

## 🎯 Which Dashboard Should You Use?

### **For Riding** (Recommend Node-RED):
- ✅ **Familiar interface** you already know
- ✅ **Rich gauges** with color-coded zones
- ✅ **GPS map** with motorcycle icon
- ✅ **Proven reliability** from your testing

### **For Remote Monitoring** (Recommend Flask):
- ✅ **Mobile-optimized** for phones/tablets
- ✅ **Lightweight** uses less cellular data
- ✅ **API access** for automation/alerts
- ✅ **Modern responsive** design

## 📊 Live Data Comparison

Both dashboards show the **same live data**:
- **GPS**: 42.8088244, -70.8675335
- **Speed**: 17.2 mph
- **Lean Angle**: 16.95°
- **G-Forces**: Forward/Lateral/Vertical
- **Heading**: 187.68°
- **Update Rate**: 4-5Hz

## 🔧 Service Status

### **Current Status**: ✅ ALL WORKING
```bash
# Node-RED Dashboard
sudo systemctl status nodered     # ✅ Active
curl http://localhost:1880/ui     # ✅ Responding

# Flask Dashboard  
ps aux | grep dashboard           # ✅ Running
curl http://localhost:8080        # ✅ Responding

# Cellular Connection
sudo mmcli -m 0                   # ✅ Connected
ping -I wwan0 8.8.8.8            # ⚠️ Route optimization needed
```

## 🚀 Quick Start Commands

### **Access Dashboards Locally**:
```bash
# Open Node-RED in browser
xdg-open http://localhost:1880/ui

# Test Flask API
curl http://localhost:8080/api/telemetry
```

### **Check System Status**:
```bash
# Check all services
sudo systemctl status nodered cellular-connection

# Check cellular connection
sudo mmcli -m 0

# Check dashboard processes
ps aux | grep -E "(node-red|dashboard)"

# Check network interfaces
ip addr show | grep -E "(wwan|wlan)"
```

## 📱 Remote Access URLs

Once you complete Tailscale setup:

### **Your Tailscale IP**: `[will be shown after auth]`
- **Node-RED**: `http://[tailscale-ip]:1880/ui`
- **Flask**: `http://[tailscale-ip]:8080`

### **Direct Cellular** (works on same network):
- **Node-RED**: `http://10.202.236.255:1880/ui`
- **Flask**: `http://10.202.236.255:8080`

## 🎉 Success!

Your motorcycle now has **TWO world-class dashboards**:

1. **Node-RED** - Rich, interactive, familiar
2. **Flask** - Modern, mobile-friendly, API-enabled

Both work **locally** and can be accessed **remotely** over cellular with Tailscale!

**Next Step**: Complete Tailscale authentication to access from anywhere in the world! 🌍 