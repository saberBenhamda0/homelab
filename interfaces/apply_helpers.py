import time
from config import BASE_URL, DURATION_BETWEEN_ATTEMPTS, session
from rich import print

def apply_dhcp_changes():
    print("[bold blue]Step 5:[/bold blue] Applying DHCP changes and waiting...")
    attempt = 1
    while True:
        print(f"[yellow]Waiting for DHCP changes to apply... (Attempt {attempt})[/yellow]")
        time.sleep(DURATION_BETWEEN_ATTEMPTS)
        apply_res = session.post(f"{BASE_URL}/api/v2/services/dhcp_server/apply")
        if apply_res.json().get("data", {}).get("applied"):
            break
        attempt += 1
    print("[bold green]DHCP changes applied.[/bold green]")

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

def apply_interface_changes():
    print("[bold blue]Step 7:[/bold blue] Applying interface changes...")
    attempt = 1
    while True:
        print(f"[yellow]Waiting for interface changes to apply... (Attempt {attempt})[/yellow]")
        time.sleep(DURATION_BETWEEN_ATTEMPTS)
        apply_res = session.post(f"{BASE_URL}/api/v2/interface/apply")
        if apply_res.json().get("data", {}).get("applied"):
            break
        attempt += 1
    print("[bold green]Interface changes applied.[/bold green]")
