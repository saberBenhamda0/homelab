import typer
from config import BASE_URL, session
from rich import print


def create_vlan_interface(lan_interface, vlan_id, name, interface_ip, interface_subnet):
    print(f"[bold blue]Step 2:[/bold blue] Creating interface for VLAN {vlan_id}...")
    interface_payload = {
        "if": f"{lan_interface}.{vlan_id}",
        "descr": name,
        "enable": True,
        "typev4": "static",
        "ipaddr": interface_ip,
        "subnet": interface_subnet,
    }
    create_res = session.post(f"{BASE_URL}/api/v2/interface", json=interface_payload)
    create_res_data = create_res.json()
    new_vlan_id = create_res_data.get("data").get("id")
    if create_res.status_code != 200:
        print("[bold red]Failed to create interface[/bold red]")
        raise typer.Exit()
    print(f"[bold green]Interface for VLAN {vlan_id} created successfully.[/bold green]")
    return new_vlan_id

def delete_interface_assignment(iface_id):
    print(f"[bold blue]Step 6:[/bold blue] Deleting interface assignment {iface_id}...")
    iface_del_res = session.delete(f"{BASE_URL}/api/v2/interface", json={"id" : iface_id, "apply":True })
    if iface_del_res.status_code == 200:
        print("[bold green]Interface deleted.[/bold green]")
    else:
        print(f"[bold red]Failed to delete interface: {iface_del_res.text}[/bold red]")
        raise typer.Exit()

def find_vlan_interface(lan_interface, vlan_id):
    vlan_if = f"{lan_interface}.{vlan_id}"
    interfaces_res = session.get(f"{BASE_URL}/api/v2/interfaces")
    interfaces = interfaces_res.json().get("data", [])
    matched_iface = next((i for i in interfaces if i.get("if") == vlan_if), None)
    if not matched_iface:
        print(f"[bold red]No interface found for VLAN {vlan_id} ({vlan_if}). Aborting.[/bold red]")
        raise typer.Exit()
    iface_id = matched_iface.get("id")
    print(f"[bold green]Found interface:[/bold green] id={iface_id}, if={vlan_if}")
    return iface_id
