# ===============================
# Imports and Global Configuration
# ===============================
from proxmoxer import ProxmoxAPI

from lxc.lxc_ops import create_container

# Imports for refactored structure
from service.service_ops import create_managed_docker, select_service
from config import ANSIBLE_CONTROL_PANEL_IP, PROXMOX_IP, TOKEN_NAME, TOKEN_VALUE, USER

# ===============================
# Proxmox Connection
# ===============================
def connect_with_token():
    """Connect to Proxmox using API token"""
    proxmox = ProxmoxAPI(
        PROXMOX_IP,
        user=f"{USER}@pam",
        token_name=TOKEN_NAME,
        token_value=TOKEN_VALUE,
        verify_ssl=False,
    )
    return proxmox

# ===============================
# Main Execution
# ===============================
if __name__ == "__main__":
    proxmox = connect_with_token()
    # Uncomment these to run examples:
    # print(get_nodes(proxmox))
    result = select_service()

    if result == "VM":
        create_container(proxmox, 10, "VM", "")
    elif result == "MANAGED_DOCKER":
        create_managed_docker(proxmox)
    # create_vm_example(proxmox)
    # create_container(proxmox, ...)
    # create_managed_docker(proxmox)
    # delete_container(proxmox, "pve", 103)
    # create_vm_example(proxmox)
    # safe_api_call()
