# Functions for creating and managing services (VM, Kubernetes, Managed Docker)
from lxc.lxc_ops import create_container
from InquirerPy import inquirer
from enum import Enum


class ServiceType(Enum):
    VM = "VM"
    KUBERNETES = "Kubernetes"
    MANAGED_DOCKER = "Managed Docker Container"

class ServiceSubType(Enum):
    WORKER_NODE = "Worker_node"
    MASTER_NODE = "Master_node"


SERVICES = [
    ServiceType.VM.name,
    ServiceType.MANAGED_DOCKER.name,
    ServiceType.KUBERNETES.name
]
 

def select_service():
    """
    Interactively prompt the user to select a service type and template.
 
    Returns a dict like:
        {"service": "Kubernetes", "flavour": "k3s"}
    or None if the user aborted or cancelled.
    """
    service = inquirer.select(
        message="Select a service to deploy",
        choices=list(SERVICES),
    ).execute()
 
    if not service:
        return None
 
    return service


def create_managed_docker(proxmox):

    count = inquirer.select(
        message="How Many Instance you want for this service",
        choices=[1, 2, 3, 4, 5, 6],
    ).execute()
 
    if not count:
        return None
    
    n = 0
    while n <= count:
        subType = ""
        if(n == 0):
            subType = ServiceSubType.MASTER_NODE.name
        else:
            subType = ServiceSubType.WORKER_NODE.name

        create_container(proxmox, 10, ServiceType.MANAGED_DOCKER.name, subType)
        n = n + 1
