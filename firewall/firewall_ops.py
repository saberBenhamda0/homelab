import time
import typer
from config import BASE_URL, DURATION_BETWEEN_ATTEMPTS, session
from rich import print


def create_firewall_rules(new_vlan_id, vlan_id):
    print("[bold blue]Step 7:[/bold blue] Creating firewall rule to block inter-VLAN communication...")
    reject_between_vlan_communication = {
        "type": "reject",
        "interface": [new_vlan_id],
        "ipprotocol": "inet",
        "protocol": "tcp/udp",
        "source": "any",
        "destination": f"!{new_vlan_id}",
        "descr": f"Block VLAN {vlan_id} from accessing other VLANs",
        "disabled": False,
        "log": True,
        "statetype": "keep state",
    }
    allow_internet = {
        "type": "pass",
        "interface": [new_vlan_id],
        "ipprotocol": "inet",
        "protocol": "tcp/udp",
        "source": f"{new_vlan_id}",
        "destination": "!RFC1918",
        "descr": f"Allow VLAN {vlan_id} to access Internet",
        "disabled": False,
        "log": False,
        "statetype": "keep state",
    }
    try:
        print("[cyan]Creating internet access rule...[/cyan]")
        firewall_rule_response = session.post(
            f"{BASE_URL}/api/v2/firewall/rule",
            json=allow_internet,
            timeout=10,
        )
        firewall_rule_response.raise_for_status()
        response_data = firewall_rule_response.json()
        if response_data.get("code") == 200 and response_data.get("status") == "ok":
            print("[bold green]✓ Internet access rule created successfully.[/bold green]")
        else:
            error_msg = response_data.get("message", "Unknown error")
            print(f"[bold red]✗ Failed to create internet rule: {error_msg}[/bold red]")
            raise typer.Exit(code=1)
        firewall_rule_response = session.post(
            f"{BASE_URL}/api/v2/firewall/rule",
            json=reject_between_vlan_communication,
            timeout=10,
        )
        firewall_rule_response.raise_for_status()
        response_data = firewall_rule_response.json()
        if response_data.get("code") == 200 and response_data.get("status") == "ok":
            print("[bold green]✓ Firewall rule created successfully.[/bold green]")
        else:
            error_msg = response_data.get("message", "Unknown error")
            print(f"[bold red]✗ Failed to create firewall rule: {error_msg}[/bold red]")
            raise typer.Exit(code=1)
    except Exception as e:
        print(f"[bold red]✗ Error creating firewall rule: {str(e)}[/bold red]")
        raise typer.Exit(code=1)

def apply_firewall_rules():
    is_firewall_rule_applied = False
    attempt = 1
    print("[bold blue]Step 8:[/bold blue] Applying firewall rules...")
    while not is_firewall_rule_applied:
        print(f"[yellow]Waiting for firewall rules to apply... (Attempt {attempt})[/yellow]")
        time.sleep(DURATION_BETWEEN_ATTEMPTS)
        apply_firewall_response = session.post(f"{BASE_URL}/api/v2/firewall/apply")
        apply_firewall = apply_firewall_response.json()
        is_firewall_rule_applied = apply_firewall.get("data").get("applied")
        attempt += 1
    print("[bold green]Firewall rules applied successfully.[/bold green]")

def delete_firewall_rules_for_interface(iface_id):
    print(f"[bold blue]Step 2:[/bold blue] Deleting firewall rules for interface {iface_id} ...")
    rules_res = session.get(f"{BASE_URL}/api/v2/firewall/rules")
    rules = rules_res.json().get("data", [])
    rules = sorted(rules, key=lambda r: r["id"], reverse=True)
    deleted_rules = 0
    for rule in rules:
        rule_interfaces = rule.get("interface", [])
        if iface_id in rule_interfaces:
            rule_tracker = rule.get("id")
            del_res = session.delete(
                f"{BASE_URL}/api/v2/firewall/rule",
                json={"id": rule_tracker}
            )
            if del_res.status_code == 200:
                print(f"[green]  ✓ Deleted firewall rule tracker={rule_tracker}[/green]")
                deleted_rules += 1
            else:
                print(f"[yellow]  ⚠ Could not delete rule tracker={rule_tracker}: {del_res.text}[/yellow]")
    print(f"[bold green]{deleted_rules} firewall rule(s) deleted.[/bold green]")

def apply_firewall_changes():
    print("[bold blue]Step 3:[/bold blue] Applying firewall changes...")
    attempt = 1
    while True:
        print(f"[yellow]Waiting for firewall changes to apply... (Attempt {attempt})[/yellow]")
        time.sleep(DURATION_BETWEEN_ATTEMPTS)
        apply_res = session.post(f"{BASE_URL}/api/v2/firewall/apply")
        if apply_res.json().get("data", {}).get("applied"):
            break
        attempt += 1
    print("[bold green]Firewall changes applied.[/bold green]")
