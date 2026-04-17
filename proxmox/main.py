# ===============================
# Imports and Global Configuration
# ===============================
from proxmoxer import ProxmoxAPI
import typer
from InquirerPy import inquirer

from lxc.lxc_ops import create_container

# Imports for refactored 
from ansible.ansible_ops import show_vlan_hosts
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

    vlan_tag_string = typer.prompt("Please entre your vlan tag")
    vlan_tag = int(vlan_tag_string)

    creating_resources = int(typer.prompt("Entre 1 for creating resources and 2 for destroying existing resources"))

    existing_vlan_hosts = show_vlan_hosts(vlan_tag, ANSIBLE_CONTROL_PANEL_IP)


    choices = [
        (item["name"], item["ip"]) for item in existing_vlan_hosts
    ]

    inquirer.select(
        message="Select a host for deleting",
        choices=choices
    ).execute()


    if creating_resources == 1:
        result = select_service()
        if result == ServiceType.VM.name:
            create_container(proxmox, vlan_tag, ServiceType.VM.name, "")
        elif result == ServiceType.MANAGED_DOCKER.name:
            create_managed_docker(proxmox, vlan_tag)
        elif result == ServiceType.KUBERNETES.name:
            created_managed_kubernetes(proxmox, vlan_tag)
