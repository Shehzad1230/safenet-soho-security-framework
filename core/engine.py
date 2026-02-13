"""
SafeNet Core - Windows WireGuard Subprocess Driver

This module provides asynchronous control of WireGuard tunnels on Windows.
It acts as the bridge between the Python control plane and the Windows OS
network stack, translating network state into WireGuard configurations.

Security Architecture:
- Zero command injection: list-based subprocess arguments only
- Absolute paths: resolves full paths for Windows services
- Non-blocking: fully async tunnel lifecycle management
- Secure cleanup: removes config files after tunnel shutdown

Windows WireGuard Enterprise Documentation:
- Install: wireguard.exe /installtunnelservice <path-to-conf>
- Uninstall: wireguard.exe /uninstalltunnelservice <tunnel-name>
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Configuration Generation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def generate_config_string(
    private_key: str,
    local_ip: str,
    listen_port: int = 51820,
    peers: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Generate a valid WireGuard INI-style configuration string.
    
    This function creates a WireGuard configuration with:
    - [Interface] section: local device configuration
    - [Peer] sections: remote peer configurations (one per peer)
    
    Args:
        private_key: Base64-encoded WireGuard private key (44 chars)
        local_ip: Local IP address with CIDR notation (e.g., "10.8.0.1/24")
        listen_port: UDP port for WireGuard to listen on (default: 51820)
        peers: List of peer dictionaries, each containing:
               - "public_key": Base64-encoded public key
               - "allowed_ips": CIDR notation IPs that can route through this peer
               - "endpoint": (Optional) "host:port" for the peer
    
    Returns:
        str: Complete WireGuard configuration in INI format
    
    Security Notes:
        - No validation of IP addresses (assumes sanitized from Pydantic)
        - No validation of keys (assumes from generate_wireguard_keys)
        - Peers list can be empty (creates interface-only config)
    
    Example:
        config = generate_config_string(
            private_key="cNJx...",
            local_ip="10.8.0.1/24",
            listen_port=51820,
            peers=[
                {
                    "public_key": "HIgo...",
                    "allowed_ips": "10.8.0.2/32",
                    "endpoint": "192.168.1.10:51820"
                }
            ]
        )
    """
    if peers is None:
        peers = []
    
    logger.info(f"Generating WireGuard config: local_ip={local_ip}, peers={len(peers)}")
    
    # Build [Interface] section
    config_lines = [
        "[Interface]",
        f"PrivateKey = {private_key}",
        f"Address = {local_ip}",
        f"ListenPort = {listen_port}",
        ""  # Blank line for readability
    ]
    
    # Build [Peer] sections
    for idx, peer in enumerate(peers):
        logger.debug(f"Adding peer {idx + 1}: {peer.get('public_key', 'N/A')[:20]}...")
        
        config_lines.append("[Peer]")
        config_lines.append(f"PublicKey = {peer['public_key']}")
        config_lines.append(f"AllowedIPs = {peer['allowed_ips']}")
        
        # Optional: Add endpoint if peer has a known address
        if "endpoint" in peer and peer["endpoint"]:
            config_lines.append(f"Endpoint = {peer['endpoint']}")
        
        # Optional: Add persistent keepalive for NAT traversal
        if "keepalive" in peer:
            config_lines.append(f"PersistentKeepalive = {peer['keepalive']}")
        
        config_lines.append("")  # Blank line between peers
    
    config_string = "\n".join(config_lines)
    
    logger.info(f"Config generated successfully: {len(config_lines)} lines")
    return config_string


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tunnel Lifecycle Management
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def start_safenet_tunnel(
    config_string: str,
    tunnel_name: str = "safenet",
    config_dir: Path = Path("data")
) -> bool:
    """
    Start a WireGuard tunnel on Windows using the enterprise wireguard.exe CLI.
    
    This function:
    1. Writes the config to a temporary .conf file
    2. Resolves the absolute path (required by Windows services)
    3. Calls `wireguard.exe /installtunnelservice <absolute-path>`
    4. Waits for the service to start
    
    Args:
        config_string: Complete WireGuard configuration (from generate_config_string)
        tunnel_name: Name of the tunnel service (default: "safenet")
        config_dir: Directory to store config file (default: data/)
    
    Returns:
        bool: True if tunnel started successfully, False otherwise
    
    Raises:
        RuntimeError: If wireguard.exe is not found or service fails to start
    
    Security Notes:
        - Uses list-based subprocess args (prevents command injection)
        - Validates config file write before calling wireguard.exe
        - No shell=True (prevents shell injection)
    
    Windows Enterprise CLI:
        wireguard.exe /installtunnelservice C:\\absolute\\path\\to\\safenet.conf
    """
    logger.info(f"Starting WireGuard tunnel: {tunnel_name}")
    
    # Ensure config directory exists
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Write config to file
    config_file = config_dir / f"{tunnel_name}.conf"
    
    try:
        logger.debug(f"Writing config to: {config_file}")
        config_file.write_text(config_string, encoding="utf-8")
        logger.info(f"Config file written: {config_file} ({len(config_string)} bytes)")
    except Exception as e:
        logger.error(f"Failed to write config file: {e}")
        raise RuntimeError(f"Config file write failed: {e}")
    
    # Resolve absolute path (Windows services require absolute paths)
    absolute_config_path = config_file.resolve()
    logger.debug(f"Resolved absolute path: {absolute_config_path}")
    
    # Validate config file exists before calling wireguard.exe
    if not absolute_config_path.exists():
        logger.error(f"Config file does not exist: {absolute_config_path}")
        raise RuntimeError(f"Config file not found: {absolute_config_path}")
    
    # Build wireguard.exe command
    # Security: List-based args prevent command injection
    wireguard_cmd = [
        "wireguard.exe",
        "/installtunnelservice",
        str(absolute_config_path)
    ]
    
    logger.info(f"Executing: {' '.join(wireguard_cmd)}")
    
    try:
        # Execute wireguard.exe asynchronously
        # CRITICAL: shell=False (default) prevents shell injection
        process = await asyncio.create_subprocess_exec(
            *wireguard_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for process to complete
        stdout, stderr = await process.communicate()
        
        # Decode output
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        
        # Check return code
        if process.returncode == 0:
            logger.info(f"Tunnel '{tunnel_name}' started successfully")
            if stdout_text:
                logger.debug(f"stdout: {stdout_text}")
            return True
        else:
            logger.error(f"Tunnel start failed (exit code: {process.returncode})")
            if stderr_text:
                logger.error(f"stderr: {stderr_text}")
            raise RuntimeError(
                f"Tunnel start failed with exit code {process.returncode}: {stderr_text}"
            )
    
    except FileNotFoundError:
        logger.error("wireguard.exe not found in system PATH")
        raise RuntimeError(
            "wireguard.exe not found. Ensure WireGuard for Windows is installed "
            "and 'C:\\Program Files\\WireGuard' is in your system PATH.\n"
            "Download: https://www.wireguard.com/install/"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during tunnel start: {e}")
        raise RuntimeError(f"Tunnel start failed: {e}")


async def stop_safenet_tunnel(
    tunnel_name: str = "safenet",
    config_dir: Path = Path("data"),
    delete_config: bool = True
) -> bool:
    """
    Stop a running WireGuard tunnel on Windows.
    
    This function:
    1. Calls `wireguard.exe /uninstalltunnelservice <tunnel-name>`
    2. Waits for the service to stop
    3. Optionally deletes the config file for security cleanup
    
    Args:
        tunnel_name: Name of the tunnel service to stop (default: "safenet")
        config_dir: Directory where config file is stored (default: data/)
        delete_config: Whether to delete the .conf file after stopping (default: True)
    
    Returns:
        bool: True if tunnel stopped successfully, False otherwise
    
    Raises:
        RuntimeError: If wireguard.exe is not found or service fails to stop
    
    Security Notes:
        - Uses list-based subprocess args (prevents command injection)
        - Securely deletes config file after tunnel shutdown
        - No shell=True (prevents shell injection)
    
    Windows Enterprise CLI:
        wireguard.exe /uninstalltunnelservice safenet
    """
    logger.info(f"Stopping WireGuard tunnel: {tunnel_name}")
    
    # Build wireguard.exe command
    # Security: List-based args prevent command injection
    wireguard_cmd = [
        "wireguard.exe",
        "/uninstalltunnelservice",
        tunnel_name
    ]
    
    logger.info(f"Executing: {' '.join(wireguard_cmd)}")
    
    try:
        # Execute wireguard.exe asynchronously
        # CRITICAL: shell=False (default) prevents shell injection
        process = await asyncio.create_subprocess_exec(
            *wireguard_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for process to complete
        stdout, stderr = await process.communicate()
        
        # Decode output
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()
        
        # Check return code
        if process.returncode == 0:
            logger.info(f"Tunnel '{tunnel_name}' stopped successfully")
            if stdout_text:
                logger.debug(f"stdout: {stdout_text}")
        else:
            logger.warning(f"Tunnel stop returned non-zero exit code: {process.returncode}")
            if stderr_text:
                logger.warning(f"stderr: {stderr_text}")
            # Don't raise error - tunnel might already be stopped
    
    except FileNotFoundError:
        logger.error("wireguard.exe not found in system PATH")
        raise RuntimeError(
            "wireguard.exe not found. Ensure WireGuard for Windows is installed "
            "and 'C:\\Program Files\\WireGuard' is in your system PATH.\n"
            "Download: https://www.wireguard.com/install/"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during tunnel stop: {e}")
        raise RuntimeError(f"Tunnel stop failed: {e}")
    
    # Cleanup: Delete config file for security
    if delete_config:
        config_file = Path(config_dir) / f"{tunnel_name}.conf"
        
        if config_file.exists():
            try:
                logger.debug(f"Deleting config file: {config_file}")
                config_file.unlink()
                logger.info(f"Config file deleted: {config_file}")
            except Exception as e:
                logger.warning(f"Failed to delete config file: {e}")
        else:
            logger.debug(f"Config file does not exist (already deleted?): {config_file}")
    
    return True


async def get_tunnel_status(tunnel_name: str = "safenet") -> Optional[Dict[str, str]]:
    """
    Check if a WireGuard tunnel is currently running.
    
    This is a helper function that uses Windows `sc query` command to check
    if the WireGuard tunnel service is running.
    
    Args:
        tunnel_name: Name of the tunnel service (default: "safenet")
    
    Returns:
        dict: Service status information, or None if service doesn't exist
              Contains keys: "state", "pid", etc.
    
    Security Notes:
        - Uses list-based subprocess args (prevents command injection)
        - No shell=True (prevents shell injection)
    
    Windows Service Query:
        sc query WireGuardTunnel$safenet
    """
    service_name = f"WireGuardTunnel${tunnel_name}"
    logger.debug(f"Querying service status: {service_name}")
    
    # Build sc query command
    # Security: List-based args prevent command injection
    sc_cmd = [
        "sc",
        "query",
        service_name
    ]
    
    try:
        # Execute sc.exe asynchronously
        process = await asyncio.create_subprocess_exec(
            *sc_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Wait for process to complete
        stdout, stderr = await process.communicate()
        
        # Decode output
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        
        # Parse output
        if process.returncode == 0 and stdout_text:
            # Service exists - parse status
            status = {}
            for line in stdout_text.split("\n"):
                if "STATE" in line:
                    # Extract state (e.g., "RUNNING", "STOPPED")
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        state_info = parts[1].strip()
                        status["state"] = state_info.split()[0] if state_info else "UNKNOWN"
            
            logger.info(f"Tunnel status: {status.get('state', 'UNKNOWN')}")
            return status if status else None
        else:
            # Service doesn't exist
            logger.debug(f"Service '{service_name}' not found")
            return None
    
    except Exception as e:
        logger.warning(f"Failed to query tunnel status: {e}")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test/Demo Code
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def _test_engine():
    """
    Test the WireGuard engine with a sample configuration.
    
    WARNING: This will attempt to create a real WireGuard tunnel on Windows.
    Only run this if you have WireGuard installed and admin privileges.
    """
    print("=" * 70)
    print("SafeNet WireGuard Engine - Test Suite")
    print("=" * 70)
    print()
    
    # Generate a sample configuration
    print("[TEST 1] Generating WireGuard config...")
    
    # NOTE: These are dummy keys for testing
    # In production, use generate_wireguard_keys() from core.keygen
    sample_private_key = "cNJxVO8VnHKwDmkYjFcSrAIvR6xBPmZqvW0yHfUZnkg="
    sample_public_key = "HIgo3OfthMXqP3i2e7yzj7WUMaKv4jEvRBDbK3i8bm8="
    
    config = generate_config_string(
        private_key=sample_private_key,
        local_ip="10.8.0.1/24",
        listen_port=51820,
        peers=[
            {
                "public_key": sample_public_key,
                "allowed_ips": "10.8.0.2/32",
                "endpoint": "192.168.1.10:51820"
            }
        ]
    )
    
    print("Config generated:")
    print("-" * 70)
    print(config)
    print("-" * 70)
    print()
    
    # Test tunnel start (ENABLED - requires admin privileges)
    print("[TEST 2] Tunnel start/stop (requires WireGuard + Admin)")
    print("Testing tunnel lifecycle...")
    print()
    
    # Tunnel operations test (ACTIVE - requires admin!):
    try:
        print("Starting tunnel...")
        await start_safenet_tunnel(config)
        print("Tunnel started!")
        
        print("Checking status...")
        status = await get_tunnel_status()
        print(f"Status: {status}")
        
        print("Stopping tunnel...")
        await stop_safenet_tunnel()
        print("Tunnel stopped!")
    except Exception as e:
        print(f"Error: {e}")
    
    print("=" * 70)
    print("Engine test complete")
    print("=" * 70)


if __name__ == "__main__":
    """
    Main entry point for engine testing.
    """
    try:
        # Add WireGuard to PATH temporarily (Windows-specific)
        if "WireGuard" not in os.environ.get("PATH", ""):
            os.environ["PATH"] += r";C:\Program Files\WireGuard"
        
        # Run async test
        asyncio.run(_test_engine())
        
    except KeyboardInterrupt:
        print("\n[INFO] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
