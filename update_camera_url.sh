#!/bin/bash
# Script to update camera URL in Node-RED flows with current IP address

# Get current IP address
IP=$(hostname -I | awk '{print $1}')
echo "Current IP address: $IP"

# Make a backup of the original file
cp enhanced_node_red_flow_with_camera.json enhanced_node_red_flow_with_camera.json.bak

# Update all references to localhost:8090 in the flow file
sed -i "s|http://[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}:8090|http://$IP:8090|g" enhanced_node_red_flow_with_camera.json
sed -i "s|http://localhost:8090|http://$IP:8090|g" enhanced_node_red_flow_with_camera.json

echo "Updated Node-RED flow with current IP address: $IP"
echo "Please import the updated flow into Node-RED:"
echo "1. Open Node-RED: http://$IP:1880/"
echo "2. Click on the menu (top-right corner) and select 'Import'"
echo "3. Click 'select a file to import'"
echo "4. Select the file: ~/enhanced_node_red_flow_with_camera.json"
echo "5. Select 'Deploy current flows' and click 'Import'"
echo "6. Click 'Deploy' in the top-right corner"

echo ""
echo "After these steps, your camera feed should be accessible at:"
echo "Dashboard: http://$IP:1880/ui"
echo "Direct camera stream: http://$IP:8090/"
