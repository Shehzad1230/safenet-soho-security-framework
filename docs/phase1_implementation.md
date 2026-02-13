# Phase 1: Environment Setup & In-Memory Cryptography Engine

## Windows PowerShell Commands for Project Scaffold

Execute these commands sequentially in PowerShell from your desired project root:

```powershell
# Navigate to your project directory
cd D:\Projects\safenet-soho-security-framework

# Create the directory structure
New-Item -ItemType Directory -Path "core" -Force
New-Item -ItemType Directory -Path "api" -Force
New-Item -ItemType Directory -Path "cli" -Force
New-Item -ItemType Directory -Path "data" -Force
New-Item -ItemType Directory -Path "certs" -Force

# Initialize __init__.py files for Python packages
New-Item -ItemType File -Path "core\__init__.py" -Force
New-Item -ItemType File -Path "api\__init__.py" -Force
New-Item -ItemType File -Path "cli\__init__.py" -Force

# Create the keygen.py file (we'll write the code next)
New-Item -ItemType File -Path "core\keygen.py" -Force

# Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# If you encounter execution policy errors, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Create requirements.txt for future dependencies
New-Item -ItemType File -Path "requirements.txt" -Force
```

## Directory Structure Verification

After running the commands, your structure should look like:

```
safenet-soho-security-framework/
├── core/
│   ├── __init__.py
│   └── keygen.py
├── api/
│   └── __init__.py
├── cli/
│   └── __init__.py
├── data/
├── certs/
├── venv/
├── reference/
│   ├── architecture.md
│   ├── phase1.md
│   └── Project SafeNet_ A Lightweight, Policy....pdf
└── requirements.txt
```

## Security Implementation Notes

### Critical Security Constraints Implemented:
1. [COMPLETE] **Zero-Disk-Key Cryptography**: Private keys are generated and held entirely in memory using `asyncio.subprocess.PIPE`
2. [COMPLETE] **Asynchronous Execution**: Non-blocking subprocess calls using `asyncio.create_subprocess_exec`
3. [COMPLETE] **Strict Input Sanitization**: Using list arguments instead of `shell=True` to prevent command injection
4. [COMPLETE] **Robust Error Handling**: Catches `FileNotFoundError`, validates return codes, and provides detailed error messages
5. [COMPLETE] **Memory-Only Key Pipeline**: Private key is piped directly from `wg genkey` stdout to `wg pubkey` stdin without touching disk

### Next Steps After Phase 1:
- Verify `wg.exe` is in system PATH
- Run the test function to validate key generation
- Ensure no `.key` files appear in the filesystem
- Proceed to Phase 2 only after validation
