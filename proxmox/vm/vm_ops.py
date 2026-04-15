# Functions related to VM operations
from shared.utils import wait_for_ip, start_vm, get_nodes, get_node_info, get_next_vmid
from ansible.ansible_ops import register_host_in_ansible
from InquirerPy import inquirer
import typer
from config import VLAN_TAG, ANSIBLE_CONTROL_PANEL_IP
import time
import sys


def get_available_templates(proxmox, node, storage=None, only_templates=False):
    """
    Get all available LXC templates for container creation.

    Returns list of LXC templates with their details.
    """
    templates = []

    # Get all storages or specific storage
    if storage:
        storages = [{"storage": storage}]
    else:
        storages = proxmox.nodes(node).storage.get()

    # Check each storage for template content
    for store in storages:
        storage_name = store["storage"]

        try:
            # Get template content from this storage
            content = proxmox.nodes(node).storage(storage_name).content.get()

            for item in content:

                # Safely get the volid and handle naming
                volid = item.get("volid", "")

                # Extract filename: handles 'local:vztmpl/ubuntu...' and 'local-lvm:base-103...'
                if "/" in volid:
                    filename = volid.split("/")[-1]
                else:
                    filename = volid.split(":")[-1]



                # Combine the checks into one condition to avoid code duplication
                is_cloud_image_container = item.get("content") == "images"
                # is_vztmpl = item.get("content") == "vztmpl"
                is_base_clone = "base-" in volid

                if only_templates:
                    if is_cloud_image_container and is_base_clone:
                        templates.append(
                            {
                                "vmid": item.get("vmid"),
                                "volid": volid,
                                "name": filename,
                                "size_mb": item.get("size", 0) / (1024**2),
                                "storage": storage_name,
                            }
                        )
                else:
                    if is_cloud_image_container:
                        # to skip pfsense firewall image
                        if item.get("vmid") == 100:
                            continue
                        templates.append(
                            {
                                "vmid": item.get("vmid"),
                                "volid": volid,
                                "name": filename,
                                "size_mb": item.get("size", 0) / (1024**2),
                                "storage": storage_name,
                            }
                        )
        except:
            # Storage doesn't have templates, skip
            pass

    return sorted(templates, key=lambda x: x["name"])

def create_vm_example(proxmox, vlan_tag, ServiceType: str, ServiceSubType):
    """Example of creating a new VM"""

    nodes = get_nodes(proxmox)
    existing_nodes = [node.get("node") for node in nodes]
    selected_node = inquirer.select(
        message="Select a Node to create vm on it :",
        choices=existing_nodes,
    ).execute()

    specs = get_node_info(proxmox, selected_node)

    vms_image = get_available_templates(proxmox, selected_node,None, False)
    existing_iso = [image.get("volid") for image in vms_image]

    container_hostname = typer.prompt("Please enter the hostname of your container")

    selected_vm = inquirer.select(
        message="Select The VM you want to create :",
        choices=existing_iso,
    ).execute()

    vm_name = typer.prompt("Please enter your the name of your vm")

    next_valid_id = get_next_vmid(proxmox)


    selected_vm_object = next(
        template
        for template in vms_image 
        if template.get("volid") == selected_vm
    )

    if "base-" in selected_vm:
        task = (
            proxmox.nodes(selected_node)
            .qemu(selected_vm_object.get("vmid"))
            .clone.post(
                newid=next_valid_id,
                full=1,
            )
        )

        # when we first create the container we need to wait until it finished because it gonna be locked.
        print("⏳ Waiting for clone to finish...")
        while True:
            task_status = proxmox.nodes(selected_node).tasks(task).status.get()
            if task_status["status"] == "stopped":
                if task_status["exitstatus"] == "OK":
                    print("✅ Clone finished!")
                    break
                else:
                    print(f"❌ Clone failed: {task_status['exitstatus']}")
                    sys.exit(1)
            time.sleep(2)
    else:

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



        # VM configuration
        vm_config = {
            "vmid": next_valid_id,
            "name": vm_name,
            "memory": int(memory_in_gb * 1024),
            "cores": cores_in_vm,
            "sockets": socket_in_vm,
            "net0": f"virtio,bridge=vmbr1,tag={vlan_tag}", # i also need to enable dhcp
            "ide2": f"{selected_vm},media=cdrom",
            "scsi0": "local-lvm:32",
            "ostype": "l26",  # Linux 2.6+ kernel
            "boot": "order=scsi0",
        }
        # # Create the VM
        proxmox.nodes(selected_node).qemu.create(**vm_config)
    # print("VM creation code is commented out. Uncomment to use.")

    # give the container a vlan tag
    proxmox.nodes(selected_node).qemu(next_valid_id).config.put(net0=f"name=eth0,bridge=vmbr1,tag={vlan_tag},ip=dhcp")

    start_vm(proxmox, selected_node, next_valid_id)

    # waiting 170 second because that is the average time for vm to start
    time.sleep(170)

    container_ip_address = wait_for_ip(proxmox, selected_node, next_valid_id, 60, "vm")

    print(container_ip_address)


    VLAN_NAME_FOR_ANSIBLE_INVENTORY = f"vlan_{vlan_tag}"

    register_host_in_ansible(container_ip_address, VLAN_NAME_FOR_ANSIBLE_INVENTORY, ANSIBLE_CONTROL_PANEL_IP, ServiceType, ServiceSubType, container_hostname)

    print(f"VM {next_valid_id} created successfully!")