# pfSense CLI Automation - Command Reference

This CLI tool provides automation for pfSense network management tasks, including VLAN, DHCP, firewall, and interface operations. The CLI is built using [Typer](https://typer.tiangolo.com/) and interacts with the pfSense API.

## Usage

Run the CLI using Python:

```sh
python pfsense_main.py [COMMAND] [OPTIONS]
```

---

## Available Commands

### 1. `setup-vlan`
Create and configure a new VLAN, including interface, DHCP, and firewall rules.

**Usage:**
```sh
python pfsense_main.py setup-vlan --vlan-id <VLAN_ID> --name <NAME> --interface_ip <IP> --interface_subnet <SUBNET> --dns_server <DNS_IP> --gateway <GATEWAY> [--range_from <START_IP>] [--range_to <END_IP>]
```

**Options:**
- `--vlan-id` (int, required): VLAN tag number to create.
- `--name` (str, required): Description/name for the VLAN.
- `--interface_ip` (str, required): IP address for the new VLAN interface.
- `--interface_subnet` (int, required): Subnet mask (as CIDR, e.g., 24).
- `--dns_server` (str, required): DNS server IP for DHCP.
- `--gateway` (str, required): Gateway IP for the VLAN.
- `--range_from` (str, optional): Start of DHCP range.
- `--range_to` (str, optional): End of DHCP range.

**What it does:**
- Validates subnet and IP addresses.
- Creates VLAN and interface.
- Enables DHCP server for the VLAN.
- Applies all changes and creates firewall rules.
- Verifies VLAN status.

---

### 2. `delete-vlan`
Delete a VLAN and all its associated configuration (firewall rules, DHCP, interface, VLAN tag).

**Usage:**
```sh
python pfsense_main.py delete-vlan --vlan-id <VLAN_ID>
```

**Options:**
- `--vlan-id` (int, required): VLAN tag number to delete.

**What it does:**
- Finds the interface for the VLAN.
- Deletes firewall rules for the interface.
- Disables DHCP server.
- Deletes the interface assignment.
- Deletes the VLAN tag.
- Verifies removal.

---

### 3. `test`
Fetch LAN interface information from pfSense.

**Usage:**
```sh
python pfsense_main.py test
```

**What it does:**
- Returns the interface dictionary for the LAN interface.

---

## Notes
- All commands interact with the pfSense API at `https://localhost:8443` using the credentials set in the script.
- Ensure the pfSense API is enabled and accessible from the machine running this CLI.
- The CLI uses self-signed certificates by default (SSL verification is disabled).

---

## Extending
The CLI is modularized. Logic for DHCP, firewall, VLAN, and interfaces is separated into service-specific modules under `proxmox/pfsense/`. You can add or modify operations by editing these modules.

---

## Requirements
- Python 3.7+
- [Typer](https://typer.tiangolo.com/)
- [Requests](https://docs.python-requests.org/)
- [Rich](https://rich.readthedocs.io/)

Install dependencies:
```sh
pip install typer requests rich
```

---

## Example
Create a VLAN 20 named "dev" with subnet 192.168.20.1/24:
```sh
python pfsense_main.py setup-vlan --vlan-id 20 --name dev --interface_ip 192.168.20.1 --interface_subnet 24 --dns_server 8.8.8.8 --gateway 192.168.20.1 --range_from 192.168.20.10 --range_to 192.168.20.100
```

Delete VLAN 20:
```sh
python pfsense_main.py delete-vlan --vlan-id 20
```
