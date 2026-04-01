# Functions related to VM operations
from shared.utils import wait_for_ip, start_vm, get_nodes, get_node_info, get_next_vmid
from pfsense.ansible.ansible_ops import register_host_in_ansible
from InquirerPy import inquirer
import typer
from config import VLAN_TAG, ANSIBLE_CONTROL_PANEL_IP


def get_available_iso_images(proxmox, node, storage=None):
    """
    Get all available ISO images for VM creation.

    Returns list of ISO images with their details.
    """
    iso_images = []

    # Get all storages or specific storage
    if storage:
        storages = [{"storage": storage}]
    else:
        storages = proxmox.nodes(node).storage.get()

    # Check each storage for ISO content
    for store in storages:
        storage_name = store["storage"]

        try:
            # Get ISO content from this storage
            content = (
                proxmox.nodes(node).storage(storage_name).content.get(content="iso")
            )

            for item in content:
                filename = item["volid"].split("/")[-1]

                iso_images.append(
                    {
                        "volid": item["volid"],  # Use this when creating VMs
                        "name": filename,
                        "size_gb": item.get("size", 0) / (1024**3),
                        "storage": storage_name,
                    }
                )
        except:
            # Storage doesn't have ISOs, skip
            pass

    return sorted(iso_images, key=lambda x: x["name"])


def create_vm_example(proxmox, vlan_tag, ServiceType: str, ServiceSubType):
    """Example of creating a new VM"""

    nodes = get_nodes(proxmox)
    existing_nodes = [node.get("node") for node in nodes]
    selected_node = inquirer.select(
        message="Select a Node to create vm on it :",
        choices=existing_nodes,
    ).execute()

    specs = get_node_info(proxmox, selected_node)

    vms_image = get_available_iso_images(proxmox, selected_node)
    existing_iso = [image.get("volid") for image in vms_image]

    container_hostname = typer.prompt("Please enter the hostname of your container")

    selected_vm = inquirer.select(
        message="Select The VM you want to create :",
        choices=existing_iso,
    ).execute()

    vm_name = typer.prompt("Please enter your the name of your vm")

    memory_in_gb = inquirer.select(
        message=f"How many GB of RAM you want in the vm (MAX: {int(specs['total_memory'])}) :",
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
    ).execute()

    socket_in_vm = inquirer.select(
        message=f"How many socket you want in the vm (max : {specs['sockets']}) :",
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
    ).execute()

    cores_in_vm = inquirer.select(
        message=f"How many cores you want in each socket in the vm (max: {specs['cores_per_socket']}) :",
        choices=[1, 2, 3, 4, 5, 6, 7, 8],
    ).execute()


    next_valid_id = get_next_vmid(proxmox)

    # VM configuration
    vm_config = {
        "vmid": next_valid_id,
        "name": vm_name,
        "memory": int(memory_in_gb * 1024),
        "cores": cores_in_vm,
        "sockets": socket_in_vm,
        "net0": f"virtio,bridge=vmbr1,tag={VLAN_TAG}", # i also need to enable dhcp
        "ide2": f"{selected_vm},media=cdrom",
        "scsi0": "local-lvm:32",
        "ostype": "l26",  # Linux 2.6+ kernel
        "boot": "order=scsi0",
    }

    # # Create the VM
    proxmox.nodes(selected_node).qemu.create(**vm_config)
    # print("VM creation code is commented out. Uncomment to use.")

    # give the container a vlan tag
    # proxmox.nodes(selected_node).qemu(next_valid_id).config.put(net0=f"name=eth0,bridge=vmbr1,tag=10,ip=dhcp")

    start_vm(proxmox, selected_node, next_valid_id)

    container_ip_address = wait_for_ip(proxmox, selected_node, next_valid_id)

    register_host_in_ansible(container_ip_address, "vlan_10", ANSIBLE_CONTROL_PANEL_IP, ServiceType, ServiceSubType, container_hostname)

    print(f"VM {next_valid_id} created successfully!")