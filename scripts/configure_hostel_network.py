#!/usr/bin/env python3
"""Interactive Ubuntu/Linux network configurator for C Block only.

Room/IP values are transcribed from the supplied C Block IP allocation PDF.
The script previews all settings and requires explicit confirmation before changes.
"""
import ipaddress
import shutil
import subprocess
import sys

GATEWAY = "172.31.68.1"
NETMASK = "255.255.254.0"
PREFIX = 23
DNS = ["172.31.100.6", "172.31.100.7", "172.31.100.8"]
PROXY_HOSTS = ["172.31.100.27", "172.31.102.29"]
PROXY_PORT = 3128

# PDF mapping: rooms 101-1328, 28 rooms per floor. The PDF skips .68.255:
# room 727=.68.254, room 728=.69.0, room 801=.69.1.
def room_ip_map():
    mapping = {}
    for floor in range(1, 14):
        for room_index in range(1, 29):
            room = floor * 100 + room_index
            ordinal = (floor - 1) * 28 + (room_index - 1)
            value = 60 + ordinal
            if value >= 255:
                value += 1  # skip 172.31.68.255 exactly as the PDF does
            second = 68 + value // 256
            last = value % 256
            # value is the third-octet-local offset from 172.31.68.0
            ip_value = ipaddress.IPv4Address("172.31.68.0") + value
            mapping[str(room)] = str(ip_value)
    return mapping

ROOMS = room_ip_map()

def run(args, check=True):
    return subprocess.run(args, check=check, text=True, capture_output=True)

def main():
    if sys.platform != "linux":
        print("ERROR: This script supports Linux/Ubuntu only.")
        return 1
    if not shutil.which("nmcli"):
        print("ERROR: NetworkManager (nmcli) was not found. This script expects Ubuntu with NetworkManager.")
        return 1

    print("\nHostel network configuration (Linux/Ubuntu)\n")
    print("Available verified hostel: C Block")
    hostel = input("Enter hostel name exactly as shown [C Block]: ").strip().lower()
    if hostel not in {"c block", "hostel c block", "c"}:
        print("ERROR: No verified IP mapping is available for that hostel. No changes made.")
        return 2

    room = input("Enter your room number (101-1328): ").strip()
    if room not in ROOMS:
        print(f"ERROR: Room {room!r} does not exist in the supplied C Block mapping. No changes made.")
        return 2

    ip = ROOMS[room]
    print("\nVerified configuration from C Block PDF")
    print(f"Hostel: C Block\nRoom: {room}\nIPv4 address: {ip}/{PREFIX}\nNetmask: {NETMASK}\nGateway: {GATEWAY}")
    print("DNS: " + ", ".join(DNS))
    print(f"Proxy entries listed in PDF: {PROXY_HOSTS[0]}:{PROXY_PORT}, {PROXY_HOSTS[1]}:{PROXY_PORT}")
    print("Note: PDF does not specify whether these are primary/backup or protocol-specific proxy endpoints.")
    print("This script configures the first listed proxy for GNOME HTTP/HTTPS proxy settings.")
    print("Proxy credentials are not embedded in this downloaded file.")

    try:
        active = run(["nmcli", "-t", "-f", "NAME,TYPE,DEVICE", "connection", "show", "--active"]).stdout.splitlines()
    except subprocess.CalledProcessError as exc:
        print("ERROR: Could not read NetworkManager connections:", exc.stderr.strip())
        return 1
    candidates = []
    for line in active:
        parts = line.split(":")
        if len(parts) >= 3 and parts[1] in {"802-3-ethernet", "802-11-wireless"} and parts[2]:
            candidates.append((parts[0], parts[2], parts[1]))

    if not candidates:
        print("ERROR: No active Wi-Fi or Ethernet connection found. No changes made.")
        return 1

    if len(candidates) == 1:
        connection, device, conn_type = candidates[0]
    else:
        print("\\nActive Wi-Fi/Ethernet connections:")
        for i, (name, dev, kind) in enumerate(candidates, 1):
            print(f"{i}. {name} ({dev}, {kind})")
        choice = input("Choose connection number: ").strip()
        if not choice.isdigit() or not 1 <= int(choice) <= len(candidates):
            print("ERROR: Invalid connection selection. No changes made.")
            return 2
        connection, device, conn_type = candidates[int(choice) - 1]

    print(f"Selected connection type: {conn_type}")

    print(f"\nNetworkManager connection: {connection} ({device})")
    print("WARNING: Applying a static IP can disconnect this device if the campus mapping/policy has changed.")
    confirm = input("Type APPLY to back up current connection settings and apply this configuration: ").strip()
    if confirm != "APPLY":
        print("Cancelled. No changes made.")
        return 0

    # Back up key settings and use them for rollback if any modification fails.
    fields = ["ipv4.method", "ipv4.addresses", "ipv4.gateway", "ipv4.dns"]
    old = {}
    try:
        for field in fields:
            old[field] = run(["nmcli", "-g", field, "connection", "show", connection]).stdout.strip()
        backup_path = f"./network-backup-{device}.txt"
        with open(backup_path, "w", encoding="utf-8") as backup:
            backup.write(f"Connection: {connection}\nDevice: {device}\n")
            for field, value in old.items():
                backup.write(f"{field}={value}\n")
        print(f"Backup saved to {backup_path}")
        run(["nmcli", "connection", "modify", connection,
             "ipv4.method", "manual", "ipv4.addresses", f"{ip}/{PREFIX}",
             "ipv4.gateway", GATEWAY, "ipv4.dns", ",".join(DNS)])
        run(["nmcli", "connection", "up", connection])
    except (subprocess.CalledProcessError, OSError) as exc:
        print("ERROR: Applying IPv4 settings failed. Attempting rollback.")
        try:
            rollback = ["nmcli", "connection", "modify", connection]
            for field, value in old.items():
                rollback.extend([field, value])
            run(rollback)
            run(["nmcli", "connection", "up", connection])
            print("Previous IPv4 settings restored.")
        except Exception as rollback_exc:
            print("WARNING: Automatic rollback failed. Use the saved backup and Ubuntu Network settings.")
            print(str(rollback_exc))
        print(str(exc))
        return 1

    # Configure GNOME desktop proxy. NetworkManager does not manage desktop proxy settings.
    if shutil.which("gsettings"):
        try:
            run(["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"])
            for proto in ("http", "https"):
                run(["gsettings", "set", f"org.gnome.system.proxy.{proto}", "host", PROXY_HOSTS[0]])
                run(["gsettings", "set", f"org.gnome.system.proxy.{proto}", "port", str(PROXY_PORT)])
            print("GNOME HTTP/HTTPS proxy set to the first proxy listed in the PDF.")
        except subprocess.CalledProcessError:
            print("WARNING: IPv4 applied, but GNOME proxy settings could not be applied. Configure proxy manually.")
    else:
        print("WARNING: gsettings not found. IPv4 applied; configure the desktop proxy manually.")

    print("\nDone. Verify campus connectivity before relying on this configuration.")
    print("If the connection fails, restore the previous settings using the backup file or Ubuntu Network settings.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
