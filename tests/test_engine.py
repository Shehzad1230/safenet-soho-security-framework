"""
SafeNet Engine Validation Test

This script validates that the Python engine can successfully control the 
Windows networking stack by creating a real WireGuard tunnel interface.

What this test does:
1. Generates a dummy WireGuard configuration
2. Creates a live WireGuard tunnel on Windows
3. Waits 30 seconds for manual verification via 'ipconfig'
4. Cleanly tears down the tunnel and removes the interface

How to verify:
- Run this script as Administrator
- When you see "TUNNEL IS UP!", open a new Command Prompt
- Type: ipconfig
- Look for: "Unknown adapter safenet" or "WireGuard Tunnel safenet"
- Verify: IPv4 Address should be 10.8.0.1
- Wait for auto-cleanup after 30 seconds

Security Note:
- Uses dummy keys (safe for testing)
- No peers configured (isolated tunnel)
- Automatically cleans up in finally block
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path (we're in tests/ directory)
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import (
    generate_config_string,
    start_safenet_tunnel,
    stop_safenet_tunnel,
    get_tunnel_status
)
from core.keygen import generate_wireguard_keys


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN TEST FUNCTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def test_engine_lifecycle():
    """
    Complete engine validation test with 30-second verification window.
    
    This test creates a real WireGuard tunnel on Windows and holds it open
    for manual verification via 'ipconfig' before automatically cleaning up.
    """
    
    print("=" * 70)
    print("SafeNet Engine Validation Test")
    print("=" * 70)
    print()
    
    # Track whether tunnel was started (for cleanup in finally block)
    tunnel_started = False
    
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 0: Pre-flight Check - Clean up any existing tunnel
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("[PRE-FLIGHT] Checking for existing tunnel...")
        existing_status = await get_tunnel_status()
        
        if existing_status:
            print("  [WARN] Found existing 'safenet' tunnel - cleaning up...")
            try:
                await stop_safenet_tunnel()
                print("  [OK] Existing tunnel removed")
                # Wait for Windows to fully clean up
                await asyncio.sleep(2)
            except Exception as cleanup_error:
                print(f"  [WARN] Cleanup failed: {cleanup_error}")
                print("  Continuing anyway...")
        else:
            print("  [OK] No existing tunnel found")
        
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 1: Generate Cryptographic Keys
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("[STEP 1] Generating WireGuard cryptographic keys...")
        print("  Using core.keygen module for real WireGuard keys")
        print()
        
        # Generate fresh keys using our Phase 1 keygen module
        private_key, public_key = await generate_wireguard_keys()
        
        print(f"  Private Key: {private_key[:20]}... (44 chars)")
        print(f"  Public Key:  {public_key[:20]}... (44 chars)")
        print("  [OK] Keys generated successfully")
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 2: Generate WireGuard Configuration
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("[STEP 2] Generating WireGuard configuration...")
        print("  Interface IP: 10.8.0.1/24")
        print("  Listen Port:  51820")
        print("  Peers:        0 (isolated tunnel for testing)")
        print()
        
        # Generate config with dummy data
        config = generate_config_string(
            private_key=private_key,
            local_ip="10.8.0.1/24",
            listen_port=51820,
            peers=[]  # No peers - isolated tunnel
        )
        
        print("  Generated Config Preview:")
        print("  " + "-" * 66)
        for line in config.split("\n")[:5]:
            print(f"  {line}")
        print("  ...")
        print("  " + "-" * 66)
        print("  [OK] Configuration generated")
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 3: Start WireGuard Tunnel (CRITICAL!)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("[STEP 3] Starting SafeNet tunnel...")
        print("  This will install the Windows service...")
        print("  Please wait 5 seconds...")
        print()
        
        await asyncio.sleep(5)
        
        # Start the tunnel (creates Windows service)
        success = await start_safenet_tunnel(config)
        
        if not success:
            raise RuntimeError("Failed to start tunnel")
        
        tunnel_started = True  # Mark for cleanup in finally block
        
        print("  [OK] Tunnel started successfully!")
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 4: Verify Tunnel Status
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("[STEP 4] Checking tunnel status...")
        status = await get_tunnel_status()
        
        if status:
            state_code = status.get('state', 'UNKNOWN')
            state_names = {
                '1': 'STOPPED',
                '2': 'START_PENDING',
                '3': 'STOP_PENDING',
                '4': 'RUNNING'
            }
            state_name = state_names.get(state_code, state_code)
            print(f"  Service State: {state_name} (code: {state_code})")
        else:
            print("  [WARN] Could not query service status")
        
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 5: VERIFICATION WINDOW (30 SECONDS)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("=" * 70)
        print(" " * 15 + "[!] TUNNEL IS UP! [!]")
        print("=" * 70)
        print()
        print("VERIFICATION INSTRUCTIONS:")
        print("-" * 70)
        print("1. Open a NEW Command Prompt (cmd) or PowerShell window")
        print("2. Type: ipconfig")
        print("3. Press Enter")
        print()
        print("WHAT TO LOOK FOR:")
        print("-" * 70)
        print("  Adapter Name:  'Unknown adapter safenet'")
        print("              OR 'WireGuard Tunnel safenet'")
        print()
        print("  IPv4 Address:  10.8.0.1")
        print()
        print("If you see that IP address, your Python backend has successfully")
        print("commanded the Windows kernel to create a secure virtual network!")
        print()
        print("=" * 70)
        print("  Auto-cleanup will run in 30 seconds...")
        print("=" * 70)
        print()
        
        # Hold the tunnel open for verification
        for remaining in range(30, 0, -1):
            print(f"\r  Seconds remaining: {remaining:02d}", end="", flush=True)
            await asyncio.sleep(1)
        
        print()
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # STEP 6: Tear Down Tunnel
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("[STEP 6] Tearing down SafeNet tunnel...")
        print("  Uninstalling Windows service...")
        print("  Deleting configuration file...")
        print()
        
        await stop_safenet_tunnel()
        tunnel_started = False  # Mark as cleaned up
        
        print("  [OK] Tunnel stopped and cleaned up")
        print()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # FINAL STATUS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("=" * 70)
        print("Engine Validation Test: COMPLETE")
        print("=" * 70)
        print()
        print("RESULTS:")
        print("  [OK] Key generation")
        print("  [OK] Config generation")
        print("  [OK] Tunnel start")
        print("  [OK] Service status check")
        print("  [OK] Tunnel stop")
        print("  [OK] Cleanup")
        print()
        print("If you verified the 10.8.0.1 IP in ipconfig, your Python engine")
        print("has SUCCESSFULLY controlled the Windows networking stack!")
        print()
        print("Phase 3 validation: COMPLETE")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Test interrupted by user (Ctrl+C)")
        print("  Cleaning up...")
        
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        
    finally:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # CLEANUP GUARANTEE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # This finally block ensures the tunnel is ALWAYS cleaned up,
        # even if the script crashes or the user presses Ctrl+C.
        # This prevents "ghost" WireGuard interfaces from lingering.
        
        if tunnel_started:
            print()
            print("[CLEANUP] Ensuring tunnel is stopped...")
            try:
                await stop_safenet_tunnel()
                print("  [OK] Cleanup complete")
            except Exception as cleanup_error:
                print(f"  [WARN] Cleanup failed: {cleanup_error}")
                print("  You may need to manually remove the tunnel:")
                print("  > wireguard.exe /uninstalltunnelservice safenet")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


if __name__ == "__main__":
    """
    Main entry point for engine validation test.
    
    Requirements:
    - Windows OS with WireGuard installed
    - Administrator privileges
    - Virtual environment activated
    
    Usage:
        python tests/test_engine.py
    """
    import os
    
    # Add WireGuard to PATH
    if "WireGuard" not in os.environ.get("PATH", ""):
        os.environ["PATH"] += r";C:\Program Files\WireGuard"
    
    print()
    print("=" * 70)
    print("IMPORTANT: This script requires Administrator privileges!")
    print("=" * 70)
    print()
    print("If you see 'Access Denied' errors, please:")
    print("  1. Close this window")
    print("  2. Right-click PowerShell/CMD")
    print("  3. Select 'Run as Administrator'")
    print("  4. Navigate to project directory")
    print("  5. Run: python tests\\test_engine.py")
    print()
    input("Press Enter to continue (or Ctrl+C to cancel)...")
    print()
    
    # Run the async test
    try:
        asyncio.run(test_engine_lifecycle())
    except KeyboardInterrupt:
        print("\n[INFO] Test cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        sys.exit(1)
