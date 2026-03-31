# ===============================
# Imports and Global Configuration
# ===============================
import typer
import requests
import time
from rich import print
from requests.auth import HTTPBasicAuth
import ipaddress
import urllib3
import subprocess
from config import BASE_URL, PASSWORD, USERNAME

app = typer.Typer()


# ===============================
# Session Setup
# ===============================
session = requests.Session()
session.auth = HTTPBasicAuth(USERNAME, PASSWORD)
session.headers.update({"Content-Type": "application/json"})
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import refactored service logic from submodules
from dhcp.dhcp_ops import enable_dhcp_server, apply_dhcp_changes, disable_dhcp_server
from firewall.firewall_ops import create_firewall_rules, apply_firewall_rules, delete_firewall_rules_for_interface, apply_firewall_changes
from vlan.vlan_ops import create_vlan, delete_vlan_entry, verify_vlan_removal, verify_vlan_status
from interfaces.interfaces_ops import create_vlan_interface, delete_interface_assignment, find_vlan_interface
from interfaces.apply_ops import apply_interface_changes

# ===============================
# Utility Functions
# ===============================
@app.command(name="test")
def get_vlan_lan():
    """
    Fetch LAN interface information from pfSense API.
    Returns the interface dict for the LAN interface.
    """
    response = session.get(f'{BASE_URL}/api/v2/interfaces')
    interfaces_json = response.json()
    interfaces = interfaces_json.get("data")
    result = next((interface for interface in interfaces if interface.get("id") == "lan"), None)
    return result

# ===============================
# VLAN Setup
# ===============================
@app.command()
def setup_vlan(
    vlan_id: int = typer.Option(..., "--vlan-id"),
    name: str = typer.Option(..., "--name"),
    interface_ip: str = typer.Option(..., "--interface_ip"),
    interface_subnet: int = typer.Option(..., "--interface_subnet"),
    dns_server: str = typer.Option(..., "--dns_server"),
    gateway: str = typer.Option(..., "--gateway"),
    range_from: str = typer.Option("", "--range_from"),
    range_to: str = typer.Option("", "--range_to"),
):
    """
    Creates a VLAN, applies it, enables DHCP, and verifies the status.
    """

    # Validate that all provided IPs are in the correct subnet
    print("[bold yellow]Validating subnet and IP addresses...[/bold yellow]")
    try:
        network = ipaddress.ip_network(
            f"{interface_ip}/{interface_subnet}", strict=False
        )
        for ip_label, ip_value in [
            ("range_from", range_from),
            ("range_to", range_to),
            ("gateway", gateway),
        ]:
            if ip_value and ipaddress.ip_address(ip_value) not in network:
                print(
                    f"[bold red]Error:[/bold red] {ip_label} ({ip_value}) is not in the subnet {network}"
                )
                raise typer.Exit()
        print(f"[bold green]Subnet validation successful:[/bold green] {network}")
    except ValueError as e:
        print(f"[bold red]Invalid IP or subnet provided:[/bold red] {e}")
        raise typer.Exit()
    # --- End validation ---


    # Fetch LAN interface info for VLAN creation
    print("[bold yellow]Fetching LAN interface info...[/bold yellow]")
    lan_info = get_vlan_lan()
    lan_interface = lan_info.get("if")
    print(f"[bold green]LAN interface detected:[/bold green] {lan_interface}")

    # Step 1: Create the VLAN on the detected LAN interface
    create_vlan(lan_interface, vlan_id, name)

    # Step 2: Create the interface for the new VLAN
    NEW_CREATED_VLAN_ID = create_vlan_interface(lan_interface, vlan_id, name, interface_ip, interface_subnet)

    # Step 3: Apply interface changes and wait for completion
    apply_interface_changes()

    # Step 4: Enable DHCP server on the new VLAN interface
    enable_dhcp_server(NEW_CREATED_VLAN_ID, range_from, range_to, dns_server, gateway, name)

    # Step 5: Apply DHCP changes and wait for completion
    apply_dhcp_changes()

    # Step 6: Verify that the VLAN is active
    vlan_exists = verify_vlan_status(vlan_id)

    # Step 7: Create firewall rules for VLAN
    create_firewall_rules(NEW_CREATED_VLAN_ID, vlan_id)

    # Step 8: Apply firewall rules and wait for completion
    apply_firewall_rules()

    # Final status message
    if vlan_exists:
        print(
            f"[bold green]Success![/bold green] VLAN {vlan_id} is active and verified. All steps completed successfully."
        )
    else:
        print(
            f"[bold red]Verification failed.[/bold red] VLAN {vlan_id} not found in active list."
        )

@app.command()
def delete_vlan(
    vlan_id: int = typer.Option(..., "--vlan-id"),
):
    """
    Deletes a VLAN and all its dependencies (firewall rules, DHCP, interface, VLAN).
    """

    # Step 1: Find the interface ID assigned to this VLAN
    lan_info = get_vlan_lan()
    lan_interface = lan_info.get("if")
    IFACE_ID = find_vlan_interface(lan_interface, vlan_id)

    # Step 2: Delete firewall rules associated with this interface
    delete_firewall_rules_for_interface(IFACE_ID)

    # Step 3: Apply firewall changes and wait
    apply_firewall_changes()

    # Step 4: disable DHCP server on this interface
    disable_dhcp_server(IFACE_ID)

    # Step 5: Apply DHCP changes and wait
    apply_dhcp_changes()

    # Step 6: Delete the interface assignment
    delete_interface_assignment(IFACE_ID)

    # Step 7: Apply interface changes and wait
    apply_interface_changes()

    # Step 8: Find and delete the VLAN entry
    delete_vlan_entry(vlan_id)

    # Step 9: Verify deletion
    verify_vlan_removal(vlan_id)

# ===============================
# Main Execution
# ===============================
if __name__ == "__main__":
    # Entry point for the CLI application
    app()