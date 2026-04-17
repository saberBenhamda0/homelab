# Functions related to LXC containers
from shared.utils import wait_for_ip
from shared.utils import _wait_for_task
from shared.utils import start_container
from shared.utils import get_nodes, get_node_info, get_next_vmid
from ansible.ansible_ops import register_host_in_ansible, unregister_host_from_ansible
from InquirerPy import inquirer
import typer
import time
import sys
from config import ANSIBLE_CONTROL_PANEL_IP




def get_available_lxc_templates(proxmox,node, storage=None):
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
                is_vztmpl = item.get("content") == "vztmpl"
                is_cloud_image_container = item.get("content") == "images"
                is_base_clone = "base-" in volid

                if is_cloud_image_container:
                    continue

                if is_vztmpl or is_base_clone:
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



def find_vmid_by_container_ip(proxmox, target_ip):
    """Find LXC container by IP address"""
    for node in proxmox.nodes.get():
        node_name = node['pve']
        
        # Get all LXC containers on this node
        for container in proxmox.nodes(node_name).lxc.get():
            vmid = container['vmid']
            
            # Get container config
            config = proxmox.nodes(node_name).lxc(vmid).config.get()
            
            # Check network interfaces for matching IP
            for key, value in config.items():
                if key.startswith('net'):
                    # IP format in config: ip=192.168.1.100/24
                    if 'ip=' in value and target_ip in value:
                        return {
                            'vmid': vmid,
                            'node': node_name,
                            'name': container.get('name', 'N/A')
                        }
    return None

def delete_container_by_ip_address(proxmox, ip_address):
    container_info = find_vmid_by_container_ip(ip_address)
    if container_info:
        print(f"Found container: {container_info}")
        
        # Delete the container
        vmid = container_info['vmid']
        node = container_info['node']
        
        # Stop if running
        proxmox.nodes(node).lxc(vmid).status.stop.post()
        
        # Delete
        proxmox.nodes(node).lxc(vmid).delete()
    else:
        print("Container not found")



def delete_container(proxmox, node: str, ctid: int, timeout: int = 60):
    """Stop and delete a container by its ID."""

    # check current status
    status = proxmox.nodes(node).lxc(ctid).status.current.get()

    ip_address = wait_for_ip(proxmox, node, ctid)

    # stop it first if running
    if status.get("status") == "running":
        print(f"Stopping container {ctid}...")
        task_id = proxmox.nodes(node).lxc(ctid).status.stop.post()
        _wait_for_task(proxmox, node, task_id, timeout)
        print(f"Container {ctid} stopped.")

    # delete the container
    print(f"Deleting container {ctid}...")
    task_id = proxmox.nodes(node).lxc(ctid).delete()
    _wait_for_task(proxmox, node, task_id, timeout)

    unregister_host_from_ansible(ip_address, "192.168.1.10")    
    print(f"Container {ctid} deleted.")



def create_container(proxmox, vlan_tag, ServiceType: str, ServiceSubType):
    """Create a new LXC container"""

    nodes = get_nodes(proxmox)
    existing_nodes = [node.get("node") for node in nodes]
    selected_node = inquirer.select(
        message="Select a Node to create container on it:",
        choices=existing_nodes,
    ).execute()

    specs = get_node_info(proxmox, selected_node)

    lxc_templates = get_available_lxc_templates(proxmox, selected_node)
    existing_templates = [template.get("volid") for template in lxc_templates]
    selected_template = inquirer.select(
        message="Select the LXC template you want to use:",
        choices=existing_templates,
    ).execute()

    container_hostname = typer.prompt("Please enter the hostname of your container")

    next_valid_id = get_next_vmid(proxmox)


    selected_template_object = next(
        template
        for template in lxc_templates
        if template.get("volid") == selected_template
    )

    if "base-" in selected_template:
        task = (
            proxmox.nodes(selected_node)
            .lxc(selected_template_object.get("vmid"))
            .clone.post(
                newid=next_valid_id,
                hostname=container_hostname,
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
            message=f"How many GB of RAM you want in the container (MAX: {int(specs['total_memory'])}) :",
            choices=[1, 2, 3, 4, 5, 6, 7, 8],
        ).execute()

        cores_in_container = inquirer.select(
            message=f"How many cores you want in the container (max: {specs['cores_per_socket'] * specs['sockets']}) :",
            choices=[1, 2, 3, 4, 5, 6, 7, 8],
        ).execute()

        disk_size = inquirer.select(
            message="Disk size in GB:",
            choices=[4, 8, 16, 32, 64, 128],
        ).execute()


        # Container configuration
        container_config = {
            "vmid": next_valid_id,
            "hostname": container_hostname,
            "ostemplate": selected_template,
            "memory": int(memory_in_gb * 1024),
            "cores": cores_in_container,
            "rootfs": f"local-lvm:{disk_size}",
            "net0": "name=eth0,bridge=vmbr1,ip=dhcp,",  # tag=10 TODO: for adding the vlan_id
            "unprivileged": 0,
            "features": "keyctl=1,nesting=1",  # required for k3s in LXC
            "start": 0,
        }
        # Create the container
        proxmox.nodes(selected_node).lxc.create(**container_config)
    
    
    # give the container a vlan tag
    proxmox.nodes(selected_node).lxc(
        next_valid_id,
    ).config.put(net0=f"name=eth0,bridge=vmbr1,tag={vlan_tag},ip=dhcp")

    start_container(proxmox, selected_node, next_valid_id)

    container_ip_address = wait_for_ip(proxmox, selected_node, next_valid_id)

    VLAN_NAME_FOR_ANSIBLE_INVENTORY = f"vlan_{vlan_tag}"

    register_host_in_ansible(container_ip_address, VLAN_NAME_FOR_ANSIBLE_INVENTORY, ANSIBLE_CONTROL_PANEL_IP, ServiceType, ServiceSubType, container_hostname)

    print(f"Container {next_valid_id} created successfully!")

