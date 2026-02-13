"""
Manual Tunnel Test Script

This script tests the full tunnel lifecycle including:
- Config generation
- Tunnel start (requires admin)
- Status check
- Tunnel stop

Run this script in PowerShell as Administrator:
    python test_tunnel_manual.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path (we're in tests/ directory, need to go up one level)
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    generate_wireguard_keys,
    generate_config_string,
    start_safenet_tunnel,
    get_tunnel_status,
    stop_safenet_tunnel
)


async def test_tunnel_lifecycle():
    """
    Complete tunnel lifecycle test.
    """
    print("=" * 70)
    print("SafeNet Phase 3 - Manual Tunnel Test")
    print("=" * 70)
    print()
    
    try:
        # Step 1: Generate keys
        print("[STEP 1] Generating WireGuard keys...")
        private_key, public_key = await generate_wireguard_keys()
        print(f"  Private Key: {private_key[:20]}...")
        print(f"  Public Key:  {public_key[:20]}...")
        print("  [OK] Keys generated\n")
        
        # Step 2: Generate config
        print("[STEP 2] Generating tunnel configuration...")
        config = generate_config_string(
            private_key=private_key,
            local_ip="10.8.0.1/24",
            listen_port=51820,
            peers=[]  # No peers for basic test
        )
        print("  Configuration:")
        print("  " + "\n  ".join(config.split("\n")[:5]))
        print("  [OK] Config generated\n")
        
        # Step 3: Start tunnel
        print("[STEP 3] Starting WireGuard tunnel...")
        print("  This will install the Windows service...")
        success = await start_safenet_tunnel(config)
        if success:
            print("  [OK] Tunnel started successfully!\n")
        else:
            print("  [FAIL] Tunnel failed to start\n")
            return False
        
        # Step 4: Check status
        print("[STEP 4] Checking tunnel status...")
        status = await get_tunnel_status()
        if status:
            state_code = status.get('state', 'UNKNOWN')
            # Windows service states: 1=STOPPED, 2=START_PENDING, 3=STOP_PENDING, 4=RUNNING
            state_names = {
                '1': 'STOPPED',
                '2': 'START_PENDING',
                '3': 'STOP_PENDING',
                '4': 'RUNNING'
            }
            state_name = state_names.get(state_code, state_code)
            print(f"  Status: {state_name} (code: {state_code})")
            
            if state_code in ['2', '4']:  # START_PENDING or RUNNING is success
                print("  [OK] Tunnel is running\n")
            else:
                print(f"  [WARN] Unexpected state: {state_name}\n")
        else:
            print("  [WARN] Could not query tunnel status\n")
        
        # Wait a bit
        print("[INFO] Waiting 3 seconds...")
        await asyncio.sleep(3)
        print()
        
        # Step 5: Stop tunnel
        print("[STEP 5] Stopping WireGuard tunnel...")
        await stop_safenet_tunnel()
        print("  [OK] Tunnel stopped and cleaned up\n")
        
        # Final status check
        print("[STEP 6] Verifying tunnel is stopped...")
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
            print(f"  Status: {state_name} (code: {state_code})")
            
            if state_code in ['1', '3']:  # STOPPED or STOP_PENDING is expected after uninstall
                print("  [OK] Tunnel is shutting down/stopped (expected)\n")
            else:
                print(f"  [WARN] Unexpected state: {state_name}\n")
        else:
            print("  [OK] Tunnel service removed\n")
        
        print("=" * 70)
        print("Manual Tunnel Test: COMPLETE [OK]")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Error during test: {e}")
        print("\nAttempting cleanup...")
        try:
            await stop_safenet_tunnel()
            print("Cleanup successful")
        except:
            print("Cleanup failed - you may need to manually remove the tunnel")
        return False


if __name__ == "__main__":
    """
    Main entry point.
    """
    import os
    
    # Add WireGuard to PATH
    if "WireGuard" not in os.environ.get("PATH", ""):
        os.environ["PATH"] += r";C:\Program Files\WireGuard"
    
    print()
    print("IMPORTANT: This script must be run as Administrator!")
    print()
    input("Press Enter to continue (or Ctrl+C to cancel)...")
    print()
    
    try:
        result = asyncio.run(test_tunnel_lifecycle())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
