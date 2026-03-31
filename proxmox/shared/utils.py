# Shared utility functions for LXC, VM, and services

import time


def get_nodes(proxmox):
    try:
        nodes = proxmox.nodes.get()
        return nodes
    except Exception as e:
        print(f"Error retrieving nodes: {e}")
        return []

def get_node_info(proxmox, node_name):
    node_info = proxmox.nodes(node_name).status.get()
    return {
        "sockets": node_info["cpuinfo"]["sockets"],
        "cores_per_socket": node_info["cpuinfo"]["cores"],
        "total_memory": node_info["memory"]["total"] // (1024**3),
    }

def get_next_vmid(proxmox):
    try:
        next_id = proxmox.cluster.nextid.get()
        return int(next_id)
    except Exception as e:
        print(f"Error getting next VMID: {e}")
        return None


def wait_for_ip(proxmox, node, vmid, timeout=60, vm_type="lxc"):
    start = time.time()
    print("getting the ip address .")
    while time.time() - start < timeout:
        try:
            if vm_type == "lxc":
                interfaces = proxmox.nodes(node).lxc(vmid).interfaces.get()
                for iface in interfaces:
                    if iface["name"] == "eth0":
                        ip = iface.get("inet")
                        if ip:
                            return ip.split("/")[0]
            else:
                # requires qemu-guest-agent running inside the VM
                interfaces = proxmox.nodes(node).qemu(vmid).agent("network-get-interfaces").get()
                for iface in interfaces.get("result", []):
                    if iface.get("name") == "eth0":
                        for addr in iface.get("ip-addresses", []):
                            if addr.get("ip-address-type") == "ipv4":
                                return addr["ip-address"]
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"VM {vmid} didn't get an IP within {timeout}s")


def start_container(proxmox, node: str, ctid: int, timeout: int = 60):
    """Start a container and wait for it to be running."""
    
    # trigger start
    task_id = proxmox.nodes(node).lxc(ctid).status.start.post()
    print("starting the container ...")

    # poll task until done
    start = time.time()
    while time.time() - start < timeout:
        task = proxmox.nodes(node).tasks(task_id).status.get()
        if task.get("status") == "stopped":  # "stopped" means task finished in Proxmox
            if task.get("exitstatus") == "OK":
                return True
            else:
                raise RuntimeError(f"Failed to start container {ctid}: {task.get('exitstatus')}")
        time.sleep(2)
    
    raise TimeoutError(f"Container {ctid} did not start within {timeout}s")

def start_vm(proxmox, node: str, vmid: int, timeout: int = 60):
    """Start a VM and wait for it to be running."""
    
    # trigger start
    task_id = proxmox.nodes(node).qemu(vmid).status.start.post()
    print("starting the vm ...")
    # poll task until done
    start = time.time()
    while time.time() - start < timeout:
        task = proxmox.nodes(node).tasks(task_id).status.get()
        if task.get("status") == "stopped":  # "stopped" means task finished in Proxmox
            if task.get("exitstatus") == "OK":
                return True
            else:
                raise RuntimeError(f"Failed to start VM {vmid}: {task.get('exitstatus')}")
        time.sleep(2)
    
    raise TimeoutError(f"VM {vmid} did not start within {timeout}s")


def _wait_for_task(proxmox, node: str, task_id: str, timeout: int = 60):
    """Poll a Proxmox task until it finishes."""
    start = time.time()
    while time.time() - start < timeout:
        task = proxmox.nodes(node).tasks(task_id).status.get()
        if task.get("status") == "stopped":
            if task.get("exitstatus") == "OK":
                return True
            else:
                raise RuntimeError(f"Task {task_id} failed: {task.get('exitstatus')}")
        time.sleep(2)
    raise TimeoutError(f"Task {task_id} did not finish within {timeout}s")

