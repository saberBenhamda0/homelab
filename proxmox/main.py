# ===============================
# Imports and Global Configuration
# ===============================
from proxmoxer import ProxmoxAPI
import typer

from lxc.lxc_ops import create_container

# Imports for refactored structure
from service.service_ops import create_managed_docker, select_service, created_managed_kubernetes
from config import ANSIBLE_CONTROL_PANEL_IP, PROXMOX_IP, TOKEN_NAME, TOKEN_VALUE, USER
from shared.utils import ServiceType

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

    vlan_tag_string = typer.prompt("Please entre your vlan tag")
    vlan_tag = int(vlan_tag_string)
    # print(get_nodes(proxmox))
    result = select_service()

    if result == ServiceType.VM.name:
        create_container(proxmox, vlan_tag, ServiceType.VM.name, "")
    elif result == ServiceType.MANAGED_DOCKER.name:
        create_managed_docker(proxmox, vlan_tag)
    elif result == ServiceType.KUBERNETES.name:
        created_managed_kubernetes(proxmox, vlan_tag)
    # create_vm_example(proxmox)
    # create_container(proxmox, ...)
    # create_managed_docker(proxmox)
    # delete_container(proxmox, "pve", 103)
    # create_vm_example(proxmox)
    # safe_api_call()
