# Project SafeNet - Phase 1 Setup Commands

## Complete Windows PowerShell Command Sequence

Copy and paste these commands into PowerShell to set up the project:

```powershell
# Navigate to project directory
cd D:\Projects\safenet-soho-security-framework

# Create directory structure
New-Item -ItemType Directory -Path "core", "api", "cli", "data", "certs" -Force

# Create Python package __init__.py files
New-Item -ItemType File -Path "core\__init__.py", "api\__init__.py", "cli\__init__.py" -Force

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# If execution policy error occurs:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Test the keygen module
python core\keygen.py
```

## Expected Output

### If WireGuard is NOT installed:
```
============================================================
SafeNet Antigravity Engine - Key Generation Test
============================================================
Testing asynchronous, in-memory WireGuard key generation...

[ERROR] Key generation failed
   The 'wg' command was not found. Please ensure WireGuard is installed...

Troubleshooting Steps:
   1. Verify WireGuard is installed...
```

### If WireGuard IS installed:
```
============================================================
SafeNet Antigravity Engine - Key Generation Test
============================================================
Testing asynchronous, in-memory WireGuard key generation...

[SUCCESS] Keys generated securely in memory.

------------------------------------------------------------
[PRIVATE KEY] (Memory Only - Never Save to Disk):
   yAnz4vIXbyf8tbgE+YQDtGgMfxXxfBqgwXuZ2YqKI0Y=

[PUBLIC KEY] (Safe to Share):
   HIgo3OfthMXqP3i2e7yzj7WUMaKv4jEvRBDbK3i8bm8=
------------------------------------------------------------

Validation Checklist:
   [X] Script ran without crashing
   [X] Two distinct 44-character keys generated
   [X] No .key files created on disk

Phase 1 Status: VALIDATED
   You may proceed to Phase 2: YAML Policy Engine
============================================================
```

## Installing WireGuard (If Needed)

1. Download: https://www.wireguard.com/install/
2. Install WireGuard for Windows
3. Add to PATH: `C:\Program Files\WireGuard`
4. Open a NEW PowerShell window
5. Verify: Run `wg` command

## Phase 1 Validation Checklist

✅ Directory structure created
✅ Virtual environment activated
✅ `core\keygen.py` runs without errors
✅ Two 44-character Base64 keys generated
✅ No `.key` files in filesystem (verify with `Get-ChildItem -Recurse -Filter *.key`)
✅ Keys held in memory only

## What Was Built

- **Secure Directory Structure**: Isolated modules for core, API, CLI, data, and certificates
- **In-Memory Keygen**: `core/keygen.py` with zero-disk-key architecture
- **Async Subprocess**: Uses `asyncio.create_subprocess_exec` for non-blocking WireGuard integration
- **Robust Error Handling**: Validates WireGuard installation and execution
- **Test Suite**: Built-in validation function for Phase 1 verification

## Next Steps

Once Phase 1 is validated, you can proceed to:
- **Phase 2**: YAML Policy Parser & AsyncIO SQLite Database
- **Phase 3**: Windows WireGuard Subprocess Driver
- **Phase 4**: FastAPI Endpoints & JWT Authentication
- **Phase 5**: Typer CLI Interface
