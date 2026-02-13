# Phase 3: The Windows Async Subprocess Driver

## Objective
To develop `core/engine.py`. This module acts as the interface between the Python control plane and the Windows OS network stack. [cite_start]It translates the parsed network state into physical WireGuard configurations and manages the Windows services asynchronously[cite: 185, 191].

## The Windows WireGuard Execution Flow
[cite_start]According to the official `wireguard-windows` enterprise documentation [cite: 209, 502][cite_start], managing the tunnel programmatically requires interacting with `wireguard.exe` directly via the shell[cite: 191].

1. **Config Generation:** Generate a standard WireGuard INI-style `.conf` string in memory.
2. [cite_start]**Secure File Write:** Windows requires a physical `.conf` file to install the service[cite: 193, 194]. We will write this file temporarily to the `data/` directory.
3. [cite_start]**Tunnel Up:** Execute `wireguard.exe /installtunnelservice C:\absolute\path\to\data\safenet.conf`[cite: 194]. This creates a virtual network adapter and starts the background service.
4. [cite_start]**Tunnel Down:** Execute `wireguard.exe /uninstalltunnelservice safenet`[cite: 196].

## Security Constraints (Defense in Depth)
1. **Zero Command Injection:** We must NEVER use `shell=True` in our subprocess calls. All arguments must be passed as strict lists to `asyncio.create_subprocess_exec` to prevent malicious device names from executing arbitrary Windows commands.
2. **Absolute Paths:** Windows services are notoriously finicky about relative paths. The engine must resolve the absolute path to the `.conf` file before passing it to `wireguard.exe`.
3. **Non-Blocking:** All subprocess calls must be `await`ed so the FastAPI server (which we build in Phase 4) never freezes while Windows brings the network adapter up.

## Architectural Components (`core/engine.py`)
* `generate_config_string(private_key, local_ip, peers)`: Formats the data into the WireGuard `[Interface]` and `[Peer]` blocks.
* [cite_start]`start_safenet_tunnel(config_string)`: Writes the string to `data/safenet.conf`, resolves the absolute path, and calls `/installtunnelservice`[cite: 193, 194].
* [cite_start]`stop_safenet_tunnel()`: Calls `/uninstalltunnelservice safenet` and cleans up the `safenet.conf` file[cite: 196].