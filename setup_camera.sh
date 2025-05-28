#!/bin/bash
# Setup Camera Streaming Service for Motorcycle Dashboard
# This script installs required dependencies and sets up the camera service

echo "🔧 Setting up camera streaming for motorcycle dashboard..."

# Install required packages
echo "📦 Installing required packages..."
sudo apt-get update
sudo apt-get install -y python3-opencv python3-pip

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install opencv-python-headless

# Create data directories
echo "📁 Creating data directories..."
mkdir -p ~/motorcycle_data/snapshots

# Make camera stream script executable
echo "🔑 Making camera script executable..."
chmod +x ~/camera_stream.py

# Set up systemd service
echo "🔄 Setting up systemd service..."
sudo cp ~/camera-stream.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-stream.service
sudo systemctl start camera-stream.service

# Import updated Node-RED flow
echo "📊 To update your Node-RED dashboard:"
echo "1. Open Node-RED at http://localhost:1880"
echo "2. Click on the menu (top-right) and select 'Import'"
echo "3. Select 'Clipboard' and paste the contents of enhanced_node_red_flow_with_camera.json"
echo "4. Click 'Import' and deploy the new flow"

echo "✅ Camera setup complete! Your camera feed should now be available in the Node-RED dashboard."
echo "📹 You can check the camera stream directly at http://localhost:8090/" 