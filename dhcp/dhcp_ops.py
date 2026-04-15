import time
import typer
from config import BASE_URL, DURATION_BETWEEN_ATTEMPTS, HTTPBasicAuth, PASSWORD, requests, session
from rich import print


def enable_dhcp_server(new_vlan_id, range_from, range_to, dns_server, gateway, name):
    dhcp_payload = {
        "interface": new_vlan_id,
        "enable": True,
        "range_from": range_from,
        "range_to": range_to,
        "dnsserver": [dns_server],
        "gateway": gateway,
        "domain": f"{name}.local",
        "domainsearchlist": [],
        "defaultleasetime": 7200,
        "maxleasetime": 86400,
    }
    try:
        response = session.post(
            f"{BASE_URL}/api/v2/services/dhcp_server",
            json=dhcp_payload
        )
        response.raise_for_status()
        print("[bold green]DHCP server configured successfully.[/bold green]")
    except Exception as e:
        print(f"[bold red]Error configuring DHCP: {e}[/bold red]")

def apply_dhcp_changes():
    print("[bold blue]Step 5:[/bold blue] Applying DHCP changes and waiting...")
    apply_dhcp_response = session.post(f"{BASE_URL}/api/v2/services/dhcp_server/apply")
    apply_dhcp = apply_dhcp_response.json()
    apply_dhcp_finished = False
    attempt = 1
    while not apply_dhcp_finished:
        print(f"[yellow]Waiting for DHCP changes to apply... (Attempt {attempt})[/yellow]")
        time.sleep(DURATION_BETWEEN_ATTEMPTS)
        apply_dhcp_response = session.post(
            f"{BASE_URL}/api/v2/services/dhcp_server/apply"
        )
        apply_dhcp = apply_dhcp_response.json()
        apply_dhcp_finished = apply_dhcp.get("data").get("applied")
        attempt += 1
    print("[bold green]DHCP changes applied successfully.[/bold green]")

def disable_dhcp_server(iface_id):
    print(f"[bold blue]Step 4:[/bold blue] Deleting DHCP server on interface {iface_id}...")
    dhcp_disable_res = session.get(f"{BASE_URL}/api/v2/services/dhcp_server", json={"id": iface_id})
    dhcp_data = dhcp_disable_res.json().get("data", {})
    dhcp_data['enable'] = False
    dhcp_del_res = session.patch(
        f"{BASE_URL}/api/v2/services/dhcp_server",
        json=dhcp_data
    )
    if dhcp_del_res.status_code == 200:
        print("[bold green]DHCP server deleted.[/bold green]")
    else:
        print(f"[yellow]DHCP delete returned {dhcp_del_res.status_code} — may not have existed.[/yellow]")
