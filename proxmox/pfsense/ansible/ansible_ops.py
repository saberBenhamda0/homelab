import subprocess
import typer
app = typer.Typer()
from rich import print
from shared.utils import ServiceType, ServiceSubType




def configure_host(ansible_ip,vlan, serviceType, serviceSubType, consul_server: str = None, k3s_control_plan: str = None):

    command = f"ansible-playbook /root/ansible/playbooks/site.yaml -i /root/ansible/inventory.yaml"

    if serviceType == ServiceType.MANAGED_DOCKER.name:
        
        if serviceSubType == ServiceSubType.WORKER_NODE.name:

            if not consul_server:
                print("[bold red]✗ consul_server is required for worker node[/bold red]")
                return
            
            command += f' --limit "{vlan}:&managed_docker:&worker_node" -e "this_consul_client=true managed_docker=true consul_server={consul_server}"'
            print("configure the worker node ...")

        elif serviceSubType == ServiceSubType.MASTER_NODE.name:
            
            command +=f' --limit "{vlan}:&managed_docker:&master_node" -e "this_consul_client=false managed_docker=true"'
            print("configure the master node ...")

    elif serviceType == ServiceType.KUBERNETES.name:
        
        if serviceSubType == ServiceSubType.WORKER_NODE.name:
            command +=f' --limit "{vlan}:&kubernetes:&worker_node" -e "k3s_worker=true master_ip={k3s_control_plan}" -u debian --become'
            print("configuring the worker node")

        elif serviceSubType == ServiceSubType.MASTER_NODE.name:
            command +=f' --limit "{vlan}:&kubernetes:&master_node" -e "k3s_master=true" -u debian --become'
            print("configure the k3s control plan node ...")
    
    elif serviceType == ServiceType.VM.name:
        print("no configuration has been done because we create a normal VM")
        return

    result = subprocess.run([
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"root@{ansible_ip}",
        f"{command}",
], capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        print(f"[bold green]✓ configuration in ansible is successful[/bold green]")
    else:
        print(result.stdout)
        print(f"[bold red]✗ Failed: {result.stderr}[/bold red]")



@app.command()
def register_host_in_ansible(
    ip: str = typer.Argument(..., help="IP address of the host to register"),
    group: str = typer.Argument(..., help="Ansible group to add the host to"),
    ansible_host: str = typer.Option("192.168.1.9", help="Ansible server IP"),
    serviceType:str = typer.Option("MANAGED_DOCKER", help="service type this vm belong to"),
    serviceSubType:str = typer.Option("worker_node", help="worker or master node ?"),
    host_name:str = typer.Option("host_name", help="worker or master node ?")
):
    """SSH into Ansible container and register the new host"""
    print(f"[bold blue]Registering {ip} in Ansible...[/bold blue]")
    
    command = ""
    # the consul server we going put in client node in managed docker service
    consul_server = None

    if serviceType == ServiceType.VM:
        command  = f"python3 /root/ansible/inventory_cli.py add --type vm --vlan {group} --name {host_name} --ip {ip}"
        print("we inside the vm condition")
    elif serviceType == ServiceType.KUBERNETES:
        command = ""
        if serviceSubType == ServiceSubType.WORKER_NODE:
            command = f"python3 /root/ansible/inventory_cli.py add --type k8s-worker  --vlan {group} --name {host_name} --ip {ip}"

        elif serviceSubType == ServiceSubType.MASTER_NODE:
            command = f"python3 /root/ansible/inventory_cli.py add --type k8s-master  --vlan {group} --name {host_name} --ip {ip}"

    elif serviceType == ServiceType.MANAGED_DOCKER:

        if serviceSubType == ServiceSubType.WORKER_NODE:
            command  = f"python3 /root/ansible/inventory_cli.py add --type docker-worker  --vlan {group} --name {host_name} --ip {ip}"

        elif serviceSubType == ServiceSubType.MASTER_NODE:
            command  = f"python3 /root/ansible/inventory_cli.py add --type docker-master  --vlan {group} --name {host_name} --ip {ip}"


    result = subprocess.run([
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"root@{ansible_host}",
        f"{command}",
    ],capture_output=True, text=True)

    if serviceType == ServiceType.MANAGED_DOCKER and serviceSubType == ServiceSubType.WORKER_NODE:
        
        get_master_ip_command = f"python3 /root/ansible/inventory_cli.py get-master-ip-cli --type docker --vlan {group}"
        get_master_ip_result = subprocess.run([
            "ssh",
            f"root@{ansible_host}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{get_master_ip_command}",
        ], capture_output=True, text=True)

        consul_server = get_master_ip_result.stdout.strip()



    if result.returncode == 0:
        print(result.stdout)
        print(f"[bold green]✓ {ip} registered in Ansible[/bold green]")
    else:
        print(result.stdout)
        print(f"[bold red]✗ Failed: {result.stderr}[/bold red]")

    hostname = "root"
    if serviceType == ServiceType.KUBERNETES:
        hostname = "debian"
    
    # configure the container that we just created
    configure_host(ansible_host,group, serviceType, serviceSubType, consul_server)

@app.command()
def unregister_host_from_ansible(
    ip: str          = typer.Argument(..., help="IP address of the host to remove"),
    ansible_host: str = typer.Option("192.168.1.9", help="Ansible server IP")
):
    """SSH into Ansible container and remove the host"""
    print(f"[bold blue]Removing {ip} from Ansible...[/bold blue]")


    result = subprocess.run([
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"root@{ansible_host}",
        f"python3 /root/ansible/inventory_cli.py remove --type ip --ip {ip}",
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        print(f"[bold green]✓ {ip} removed from Ansible[/bold green]")
    else:
        print(result.stdout)
        print(f"[bold red]✗ Failed: {result.stderr}[/bold red]")
