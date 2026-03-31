import time
from config import BASE_URL, DURATION_BETWEEN_ATTEMPTS, session
from rich import print


def apply_interface_changes():
    print("[bold blue]Step 3:[/bold blue] Applying interface changes...")
    apply_interface_response = session.post(f"{BASE_URL}/api/v2/interface/apply")
    apply_interface = apply_interface_response.json()
    is_apply_finished = False
    attempt = 1
    while not is_apply_finished:
        print(f"[yellow]Waiting for interface changes to apply... (Attempt {attempt})[/yellow]")
        time.sleep(DURATION_BETWEEN_ATTEMPTS)
        apply_interface_response = session.post(f"{BASE_URL}/api/v2/interface/apply")
        apply_interface = apply_interface_response.json()
        is_apply_finished = apply_interface.get("data").get("applied")
        attempt += 1
    print("[bold green]Interface changes applied successfully.[/bold green]")
