import typer
from config import BASE_URL, session
from rich import print


def create_vlan(lan_interface, vlan_id, name):
    print(f"[bold blue]Step 1:[/bold blue] Creating The VLAN {vlan_id} on {lan_interface}...")
    vlan_creation_payload = {
        "if": lan_interface,
        "tag": vlan_id,
        "descr": name,
    }
    create_res = session.post(
        f"{BASE_URL}/api/v2/interface/vlan", json=vlan_creation_payload
    )
    if create_res.status_code != 200:
        print("[bold red]Failed to create VLAN interface[/bold red]")
        raise typer.Exit()
    print(f"[bold green]VLAN {vlan_id} created successfully.[/bold green]")

def delete_vlan_entry(vlan_id):
    print(f"[bold blue]Step 8:[/bold blue] Deleting VLAN tag {vlan_id}...")
    vlans_res = session.get(f"{BASE_URL}/api/v2/interface/vlans")
    vlans = vlans_res.json().get("data", [])
    vlan_entry = next((v for v in vlans if v.get("tag") == vlan_id), None)
    if not vlan_entry:
        print(f"[yellow]VLAN tag {vlan_id} not found — may already be deleted.[/yellow]")
    else:
        vlan_internal_id = vlan_entry.get("id")
        vlan_del_res = session.delete(f"{BASE_URL}/api/v2/interface/vlan", json={"id": vlan_internal_id})
        if vlan_del_res.status_code == 200:
            print(f"[bold green]VLAN {vlan_id} deleted.[/bold green]")
        else:
            print(f"[bold red]Failed to delete VLAN: {vlan_del_res.text}[/bold red]")
            raise typer.Exit()

def verify_vlan_removal(vlan_id):
    print("[bold blue]Step 9:[/bold blue] Verifying VLAN removal...")
    check_res = session.get(f"{BASE_URL}/api/v2/interface/vlan")
    vlans_after = check_res.json().get("data", [])
    still_exists = any(v.get("tag") == vlan_id for v in vlans_after)
    if still_exists:
        print(f"[bold red]Verification failed.[/bold red] VLAN {vlan_id} still appears in the list.")
    else:
        print(f"[bold green]Success![/bold green] VLAN {vlan_id} fully removed and verified.")

def verify_vlan_status(vlan_id):
    """
    Verify that the VLAN is active.
    """
    print("[bold blue]Step 6:[/bold blue] Verifying VLAN status...")
    check_res = session.get(f"{BASE_URL}/api/v2/interface/vlans")
    vlans = check_res.json().get("data")
    vlan_exists = any(v.get("tag") == vlan_id for v in vlans)
    return vlan_exists
