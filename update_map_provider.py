#!/usr/bin/env python3
"""
Update map provider in Node-RED to show more detailed maps
"""

import requests
import json
import sys

NODE_RED_URL = "http://localhost:1880"

def update_map_config():
    """Update the worldmap node configuration"""
    try:
        # Get current flows
        response = requests.get(
            f"{NODE_RED_URL}/flows",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to get current flows: {response.status_code}")
            return False
            
        flows = response.json()
        
        # Load improved map config
        with open('improved_map_config.json', 'r') as f:
            new_map_config = json.load(f)
        
        # Find all worldmap nodes and update them
        updated = False
        
        for i, node in enumerate(flows):
            if node.get('type') == 'worldmap':
                print(f"🗺️ Found worldmap node: {node.get('id')}")
                
                # Keep the node's ID and z-coordinate
                node_id = node.get('id')
                node_z = node.get('z')
                
                # Update with new config while preserving id and z
                new_map_config['id'] = node_id
                new_map_config['z'] = node_z
                
                # Update node with improved config
                flows[i] = new_map_config
                updated = True
                print(f"✅ Updated worldmap node: {node_id}")
                
                # Add a custom button to switch map layers
                add_map_layer_buttons(flows, node_z)
        
        if not updated:
            print("❌ No worldmap nodes found to update")
            return False
        
        # Deploy updated flows
        response = requests.post(
            f"{NODE_RED_URL}/flows",
            json=flows,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in [200, 204]:
            print(f"❌ Failed to deploy flows: {response.status_code}")
            return False
            
        print("✅ Successfully updated map provider!")
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def add_map_layer_buttons(flows, dashboard_z):
    """Add buttons to switch between map layers"""
    # Check if map layer buttons already exist
    for node in flows:
        if node.get('id') == 'map-layer-buttons':
            print("✅ Map layer buttons already exist")
            return
    
    # Find the GPS info group
    gps_info_id = None
    for node in flows:
        if node.get('type') == 'ui_group' and node.get('name') == 'GPS Status & Location':
            gps_info_id = node.get('id')
            break
    
    if not gps_info_id:
        print("❌ Could not find GPS Status & Location group")
        return
    
    # Create buttons template
    buttons_template = {
        "id": "map-layer-buttons",
        "type": "ui_template",
        "z": dashboard_z,
        "group": gps_info_id,
        "name": "Map Layer Selector",
        "order": 3,
        "width": 0,
        "height": 0,
        "format": """
<div style="display: flex; flex-wrap: wrap; gap: 5px; margin: 5px 0;">
  <button onclick="setMapLayer('OSM')" style="flex: 1; padding: 5px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; min-width: 80px;">
    OpenStreetMap
  </button>
  <button onclick="setMapLayer('OSMG')" style="flex: 1; padding: 5px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; min-width: 80px;">
    OSM German
  </button>
  <button onclick="setMapLayer('EsriS')" style="flex: 1; padding: 5px; background: #FF9800; color: white; border: none; border-radius: 4px; cursor: pointer; min-width: 80px;">
    ESRI Streets
  </button>
  <button onclick="setMapLayer('EsriT')" style="flex: 1; padding: 5px; background: #795548; color: white; border: none; border-radius: 4px; cursor: pointer; min-width: 80px;">
    ESRI Terrain
  </button>
</div>

<script>
  function setMapLayer(layer) {
    // Send the layer change command to the worldmap
    fetch('/worldmap/layer/' + layer)
      .then(response => {
        if(response.ok) {
          console.log('Map layer changed to', layer);
        }
      })
      .catch(error => {
        console.error('Error changing map layer:', error);
      });
  }
</script>
        """,
        "storeOutMessages": True,
        "fwdInMessages": True,
        "resendOnRefresh": True,
        "templateScope": "local",
        "className": ""
    }
    
    # Add button template to flows
    flows.append(buttons_template)
    print("✅ Added map layer selection buttons")

if __name__ == "__main__":
    print("🗺️ Updating map provider in Node-RED...")
    if update_map_config():
        print("\n✅ MAP PROVIDER UPDATED!")
        print("You now have access to multiple detailed map layers:")
        print("  • OpenStreetMap (default) - Standard detailed map")
        print("  • OSM German Style - Alternative styling")
        print("  • ESRI Streets - Detailed street maps")
        print("  • ESRI Terrain - Topographic map with terrain details")
        print("\n🔄 You can switch between map layers using the new buttons")
        print("   in the GPS Status section of your dashboard.")
        print("\n🚀 Access your dashboard at: http://localhost:1880/ui")
    else:
        sys.exit(1) 