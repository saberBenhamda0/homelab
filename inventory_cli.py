import typer
from ruamel.yaml import YAML
import subprocess
import time
import sys

app = typer.Typer()
yaml = YAML()
yaml.preserve_quotes = True

INVENTORY_FILE = "/root/ansible/inventory.yaml"
SSH_KEY   = "~/.ssh/id_rsa"


# # ── setup ────────────────────────────────────────────────────────────────────
# python inventory_cli.py setup

# # ── vlan ─────────────────────────────────────────────────────────────────────
# python inventory_cli.py add    --type vlan --name vlan20
# python inventory_cli.py add    --type vlan --name vlan30
# python inventory_cli.py add    --type vlan --name vlan40
# python inventory_cli.py remove --type vlan --name vlan40

# # ── vm ───────────────────────────────────────────────────────────────────────
# python inventory_cli.py add    --type vm --vlan vlan40 --name vm-1 --ip 10.10.40.11
# python inventory_cli.py add    --type vm --vlan vlan40 --name vm-2 --ip 10.10.40.12
# python inventory_cli.py remove --type vm --vlan vlan40 --name vm-1

# # ── managed docker ───────────────────────────────────────────────────────────
# python inventory_cli.py add    --type docker       --vlan vlan30 --master-ip 10.10.30.10 --worker-ip 10.10.30.11
# python inventory_cli.py add    --type docker-worker --vlan vlan30 --name worker-2 --ip 10.10.30.12
# python inventory_cli.py add    --type docker-master --vlan vlan30 --name master-2 --ip 10.10.30.13
# python inventory_cli.py remove --type docker-worker  --vlan vlan30 --name worker-2
# python inventory_cli.py remove --type docker-master  --vlan vlan30
# python inventory_cli.py remove --type docker-workers --vlan vlan30
# python inventory_cli.py remove --type docker         --vlan vlan30

# # ── kubernetes ───────────────────────────────────────────────────────────────
# python inventory_cli.py add    --type kubernetes --vlan vlan20 --master-ip 10.10.20.10 --worker-ip 10.10.20.11
# python inventory_cli.py add    --type k8s-worker  --vlan vlan20 --name worker-2 --ip 10.10.20.12
# python inventory_cli.py add    --type k8s-master  --vlan vlan20 --name worker-2 --ip 10.10.20.12 
# python inventory_cli.py remove --type k8s-worker  --vlan vlan20 --name worker-2
# python inventory_cli.py remove --type k8s-workers --vlan vlan20
# python inventory_cli.py remove --type k8s-masters --vlan vlan20
# python inventory_cli.py remove --type kubernetes  --vlan vlan20

# # ── utility ──────────────────────────────────────────────────────────────────
# python inventory_cli.py remove --type ip --ip 10.10.30.12


def load():
    with open(INVENTORY_FILE) as f:
        return yaml.load(f) or {}


def save(data):
    with open(INVENTORY_FILE, "w") as f:
        yaml.dump(data, f)


# =======================
# vlan
# =======================
def add_vlan(data, vlan_name: str):
    data.setdefault("all", {}).setdefault("children", {}).setdefault(vlan_name, {})

def remove_vlan(data, vlan_name: str):
    data["all"]["children"].pop(vlan_name, None)


# =======================
# VMs
# =======================
def add_vm(data, vlan: str, vm_name: str, ansible_host: str):
    (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("VMs", {})
            .setdefault("hosts", {})
    )[vm_name] = {"ansible_host": ansible_host}

def remove_vm(data, vlan: str, vm_name: str):
    data["all"]["children"][vlan]["children"]["VMs"]["hosts"].pop(vm_name, None)

def remove_all_vms(data, vlan: str):
    data["all"]["children"].pop(vlan, None)


# =======================
# managed docker
# =======================
def add_managed_docker(data, vlan: str, master_ip: str, worker_ip: str):
    base = (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("managed_docker", {})
            .setdefault("children", {})
    )
    base.setdefault("master_node", {}).setdefault("hosts", {})["master-1"] = {"ansible_host": master_ip}
    base.setdefault("worker_node", {}).setdefault("hosts", {})["worker-1"] = {"ansible_host": worker_ip}

def add_docker_worker(data, vlan: str, worker_name: str, ansible_host: str):
    (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("managed_docker", {})
            .setdefault("children", {})
            .setdefault("worker_node", {})
            .setdefault("hosts", {})
    )[worker_name] = {"ansible_host": ansible_host}

def add_docker_master(data, vlan: str, worker_name: str, ansible_host: str):
    (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("managed_docker", {})
            .setdefault("children", {})
            .setdefault("master_node", {})
            .setdefault("hosts", {})
    )[worker_name] = {"ansible_host": ansible_host}

def remove_docker_worker(data, vlan: str, worker_name: str):
    data["all"]["children"][vlan]["children"]["managed_docker"]["children"]["worker_node"]["hosts"].pop(worker_name, None)

def remove_docker_master(data, vlan: str, worker_name: str):
    data["all"]["children"][vlan]["children"]["managed_docker"]["children"]["master_node"]["hosts"].pop(worker_name, None)

def remove_all_docker_workers(data, vlan: str):
    data["all"]["children"][vlan]["children"]["managed_docker"]["children"].pop("worker_node", None)

def remove_docker_master(data, vlan: str):
    data["all"]["children"][vlan]["children"]["managed_docker"]["children"].pop("master_node", None)

def delete_managed_docker(data, vlan: str):
    data["all"]["children"][vlan]["children"].pop("managed_docker", None)


# =======================
# kubernetes
# =======================
def add_kubernetes(data, vlan: str, master_ip: str, worker_ip: str):
    base = (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("kubernetes", {})
            .setdefault("children", {})
    )
    base.setdefault("master_node", {}).setdefault("hosts", {})["master-1"] = {"ansible_host": master_ip}
    base.setdefault("worker_node", {}).setdefault("hosts", {})["worker-1"] = {"ansible_host": worker_ip}

def add_kubernetes_worker(data, vlan: str, worker_name: str, ansible_host: str):
    (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("kubernetes", {})
            .setdefault("children", {})
            .setdefault("worker_node", {})
            .setdefault("hosts", {})
    )[worker_name] = {"ansible_host": ansible_host}

def add_kubernetes_master(data, vlan: str, master_name: str, ansible_host: str):
    (
        data.setdefault("all", {})
            .setdefault("children", {})
            .setdefault(vlan, {})
            .setdefault("children", {})
            .setdefault("kubernetes", {})
            .setdefault("children", {})
            .setdefault("master_node", {})
            .setdefault("hosts", {})
    )[master_name] = {"ansible_host": ansible_host}

def remove_kubernetes_worker(data, vlan: str, worker_name: str):
    data["all"]["children"][vlan]["children"]["kubernetes"]["children"]["worker_node"]["hosts"].pop(worker_name, None)

def remove_kubernetes_masters(data, vlan: str):
    data["all"]["children"][vlan]["children"]["kubernetes"]["children"].pop("master_node", None)

def remove_kubernetes_workers(data, vlan: str):
    data["all"]["children"][vlan]["children"]["kubernetes"]["children"].pop("worker_node", None)

def remove_kubernetes(data, vlan: str):
    data["all"]["children"][vlan]["children"].pop("kubernetes", None)


# =======================
# utility
# =======================
def remove_by_ip(data, ansible_host: str):
    def _remove(node):
        if not isinstance(node, dict):
            return
        for key, value in list(node.items()):
            if isinstance(value, dict):
                if value.get("ansible_host") == ansible_host:
                    del node[key]
                    return
                _remove(value)
    _remove(data)


def setup_inventory(data):
    data.setdefault("all", {}).setdefault("children", {})["lan_infra"] = {
        "hosts": {
            "ansible":       {"ansible_host": "192.168.1.10", "ansible_user": "root"},
            "pfsense":       {"ansible_host": "192.168.1.1",  "ansible_user": "root"},
            "control-panel": {"ansible_host": "192.168.1.9",  "ansible_user": "root"},
        }
    }


# =======================
# CLI commands
# =======================
@app.command()
def add(
    type: str      = typer.Option(..., "--type", "-t", help="vm | docker | kubernetes | vlan | docker-worker | k8s-worker"),
    vlan: str      = typer.Option(None, "--vlan", "-v", help="target VLAN (e.g. vlan30)"),
    ip: str        = typer.Option(None, "--ip",        help="ansible_host IP"),
    name: str      = typer.Option(None, "--name",      help="host/vlan name"),
    master_ip: str = typer.Option(None, "--master-ip", help="master node IP (docker / kubernetes)"),
    worker_ip: str = typer.Option(None, "--worker-ip", help="worker node IP (docker / kubernetes)"),
):
    data = load()
    t = type.lower()

    if t == "vm":
        assert vlan and ip and name, "--vlan, --ip and --name required"
        add_vm(data, vlan, name, ip)
        verify_adding(ip)

    elif t == "vlan":
        assert name, "--name required"
        add_vlan(data, name)

    elif t == "docker":
        assert vlan and master_ip and worker_ip, "--vlan, --master-ip and --worker-ip required"
        add_managed_docker(data, vlan, master_ip, worker_ip)

    elif t == "docker-worker":
        assert vlan and ip and name, "--vlan, --ip and --name required"
        add_docker_worker(data, vlan, name, ip)
        verify_adding(ip)

    elif t == "docker-master":
        assert vlan and ip and name, "--vlan, --ip and --name required"
        add_docker_master(data, vlan, name, ip)
        verify_adding(ip)

    elif t == "kubernetes":
        assert vlan and master_ip and worker_ip, "--vlan, --master-ip and --worker-ip required"
        add_kubernetes(data, vlan, master_ip, worker_ip)

    elif t == "k8s-worker":
        assert vlan and ip and name, "--vlan, --ip and --name required"
        add_kubernetes_worker(data, vlan, name, ip)
        verify_adding(ip)

    elif t == "k8s-master":
        assert vlan and ip and name, "--vlan, --ip and --name required"
        add_kubernetes_master(data, vlan, name, ip)
        verify_adding(ip)

    else:
        typer.echo(f"Unknown type: {type}"); raise typer.Exit(1)

    save(data)
    typer.echo(f"✔  Added [{t}]")


@app.command()
def remove(
    type: str = typer.Option(..., "--type", "-t", help="vm | vlan | docker | docker-worker | docker-master | docker-workers | k8s-worker | k8s-workers | k8s-masters | kubernetes | ip"),
    vlan: str = typer.Option(None, "--vlan", "-v", help="target VLAN (e.g. vlan30)"),
    name: str = typer.Option(None, "--name", help="host/vlan name to remove"),
    ip: str   = typer.Option(None, "--ip",   help="IP address to remove"),
):
    data = load()
    t = type.lower()

    if t == "vm":
        assert vlan and name, "--vlan and --name required"
        remove_vm(data, vlan, name)

    elif t == "vlan":
        assert name, "--name required"
        remove_vlan(data, name)

    elif t == "docker":
        assert vlan, "--vlan required"
        delete_managed_docker(data, vlan)

    elif t == "docker-worker":
        assert vlan and name, "--vlan and --name required"
        remove_docker_worker(data, vlan, name)

    elif t == "docker-master":
        assert vlan, "--vlan required"
        remove_docker_master(data, vlan)

    elif t == "docker-workers":
        assert vlan, "--vlan required"
        remove_all_docker_workers(data, vlan)

    elif t == "k8s-worker":
        assert vlan and name, "--vlan and --name required"
        remove_kubernetes_worker(data, vlan, name)

    elif t == "k8s-workers":
        assert vlan, "--vlan required"
        remove_kubernetes_workers(data, vlan)

    elif t == "k8s-masters":
        assert vlan, "--vlan required"
        remove_kubernetes_masters(data, vlan)

    elif t == "kubernetes":
        assert vlan, "--vlan required"
        remove_kubernetes(data, vlan)

    elif t == "ip":
        assert ip, "--ip required"
        remove_by_ip(data, ip)
        verify_removing(ip)

    else:
        typer.echo(f"Unknown type: {type}"); raise typer.Exit(1)


    
    save(data)
    typer.echo(f"✔  Removed [{t}]")


@app.command()
def setup():
    """Initialize the base inventory (lan_infra group)."""
    data = load()
    setup_inventory(data)
    save(data)
    typer.echo("✔  Inventory initialized")


# Example usage for get_master_ip:
# python inventory_cli.py get-master-ip --type docker --vlan vlan30
# python inventory_cli.py get-master-ip --type kubernetes --vlan vlan20

# =======================
# Utility: Get master node IP
# =======================
def get_master_ip(data, type: str, vlan: str):
    """
    Retrieve the master node IP address for docker or kubernetes in the given VLAN.
    """
    t = type.lower()
    if t == "docker":
        try:
            return data["all"]["children"][vlan]["children"]["managed_docker"]["children"]["master_node"]["hosts"]["master-1"]["ansible_host"]
        except (KeyError, TypeError):
            return None
    elif t == "kubernetes":
        try:
            return data["all"]["children"][vlan]["children"]["kubernetes"]["children"]["master_node"]["hosts"]["master-1"]["ansible_host"]
        except (KeyError, TypeError):
            return None
    else:
        return None

@app.command()
def get_master_ip_cli(
    type: str = typer.Option(..., "--type", "-t", help="docker | kubernetes"),
    vlan: str = typer.Option(..., "--vlan", "-v", help="target VLAN (e.g. vlan30)"),
):
    """
    Get the master node IP address for docker or kubernetes in the given VLAN.
    """
    data = load()
    ip = get_master_ip(data, type, vlan)
    if ip:
        typer.echo(f"{ip}")
    else:
        typer.echo(f"Master node IP not found for {type} in {vlan}")


def verify_removing(IP):
    # ── Step 4: Remove SSH known_hosts entry ─────────
    subprocess.run(["ssh-keygen", "-R", IP], stderr=subprocess.DEVNULL)
    print(f"✅ Removed {IP} from known_hosts")

    # ── Step 5: Verify removal ────────────────────────
    result = subprocess.run(["grep", "-q", f"^{IP}$", INVENTORY_FILE])
    if result.returncode != 0:
        print(f"✅ {IP} successfully removed from Ansible")
    else:
        print(f"❌ Something went wrong, {IP} still in inventory")
        sys.exit(1)


def verify_adding(IP):

    # ── Step 2: Wait for SSH to be ready ─────────────
    print(f"⏳ Waiting for SSH on {IP}...")
    while True:
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=3",
            f"root@{IP}", "exit"],
            capture_output=True
        )
        if result.returncode == 0:
            break
        print("retrying...")
        time.sleep(2)
    print(f"✅ SSH is up!")

    # ── Step 3: Copy SSH key ──────────────────────────
    subprocess.run(["ssh-copy-id", "-i", SSH_KEY, f"root@{IP}"])    
    print(f"✅ SSH key copied to {IP}")

    # ── Step 4: Test Ansible connection ───────────────
    subprocess.run(["ansible", "-i", INVENTORY_FILE, IP, "-m", "ping"])
    print(f"✅ {IP} is ready in Ansible!")

if __name__ == "__main__":
    app()
