import os
import sys

# Hardcoded infrastructure details
PROXMOX_IP = "192.168.176.133"
USER = "root"
TOKEN_NAME = "root01"
ANSIBLE_CONTROL_PANEL_IP = "192.168.1.9"
VLAN_TAG = "10"

# Load ONLY the sensitive token from environment variables
TOKEN_VALUE = os.getenv("PROXMOX_TOKEN")

# Safety Check: Stop the script if the token is missing
if not TOKEN_VALUE:
    print("ERROR: Environment variable 'PROXMOX_TOKEN_VALUE' is not set.")
    sys.exit(1)

print(f"Successfully loaded token for {USER}@{PROXMOX_IP}")
