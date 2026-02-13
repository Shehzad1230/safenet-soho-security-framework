This is the perfect approach. In cybersecurity and systems engineering, moving too fast introduces catastrophic vulnerabilities. By breaking the "Antigravity" architecture into minute, verifiable steps, we ensure your foundation is rock-solid.

We will build this in strict phases. **Do not move to Phase 2 until you have perfectly validated Phase 1.**

Here is the roadmap for our build:

* **Phase 1 (Today):** Environment Setup & In-Memory Cryptography Engine.
* **Phase 2:** The YAML Policy Parser & Asyncio SQLite Database.
* **Phase 3:** The Windows `wireguard.exe` Async Subprocess Driver.
* **Phase 4:** The FastAPI Endpoints & JWT Authentication.
* **Phase 5:** The Typer CLI interface.

Let's begin with Phase 1.

---

### Phase 1: Environment Setup & In-Memory Cryptography

Before we write the API, we must prove we can securely generate WireGuard keys using Python without ever saving the private key to your Windows hard drive.

#### Step 1.1: System Prerequisites

1. **Install WireGuard for Windows:** Download and install the official client from wireguard.com. This installs the `wg.exe` and `wireguard.exe` command-line tools.
2. **Verify PATH:** Open your Windows Command Prompt (cmd) and type `wg`. If it says "command not found", you must add `C:\Program Files\WireGuard` to your Windows System PATH environment variable.
3. **Install Python 3.10+:** Ensure you have a modern, asynchronous-capable version of Python installed.

#### Step 1.2: Initialize the Project Structure

Open your terminal (PowerShell or Command Prompt) and run these exact commands to create your secure directory structure:

```bash
mkdir safenet
cd safenet
mkdir core api cli data certs
type nul > core\__init__.py
type nul > core\keygen.py

```

Create your virtual environment to keep dependencies isolated:

```bash
python -m venv venv
venv\Scripts\activate

```

#### Step 1.3: Write the Secure Key Generator (`core/keygen.py`)

This is the heart of your security. The standard way to generate keys is by writing them to a file (e.g., `wg genkey > privatekey`). **We will not do that.**

Instead, we will use `asyncio.create_subprocess_exec` to execute the `wg` commands and capture the output directly into Python's memory using `PIPE`. By using `communicate(input=...)`, we can securely pass the generated private key directly into the public key generator via standard input.

Open `core/keygen.py` in your code editor and paste this exact code:

```python
import asyncio
from asyncio.subprocess import PIPE

async def generate_wireguard_keys() -> tuple[str, str]:
    """
    Asynchronously generates a WireGuard private and public key pair.
    The keys are held strictly in memory and never written to disk.
    """
    try:
        # 1. Generate Private Key
        # This calls 'wg genkey' and captures the standard output in memory
        proc_priv = await asyncio.create_subprocess_exec(
            "wg", "genkey",
            stdout=PIPE,
            stderr=PIPE
        )
        stdout_priv, stderr_priv = await proc_priv.communicate()
        
        if proc_priv.returncode != 0:
            raise RuntimeError(f"Failed to generate private key: {stderr_priv.decode()}")
            
        private_key = stdout_priv.decode('utf-8').strip()

        # 2. Generate Public Key from Private Key
        # We pass the private_key string directly into 'wg pubkey' via standard input
        proc_pub = await asyncio.create_subprocess_exec(
            "wg", "pubkey",
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE
        )
        stdout_pub, stderr_pub = await proc_pub.communicate(input=private_key.encode('utf-8'))
        
        if proc_pub.returncode != 0:
            raise RuntimeError(f"Failed to generate public key: {stderr_pub.decode()}")
            
        public_key = stdout_pub.decode('utf-8').strip()

        return private_key, public_key

    except FileNotFoundError:
        raise RuntimeError("The 'wg' command was not found. Is WireGuard installed and in your system PATH?")

# --- Validation Block ---
# This block only runs if you execute this file directly.
async def _test_keygen():
    print("🚀 Testing Antigravity Key Generation...")
    try:
        priv, pub = await generate_wireguard_keys()
        print("✅ Success!")
        print(f"🔒 Private Key (Memory Only): {priv}")
        print(f"🌍 Public Key (Safe to share): {pub}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(_test_keygen())

```

#### Step 1.4: Validate Phase 1

We must test this script immediately to ensure your Windows machine allows Python to interact with the WireGuard executables asynchronously.

In your terminal (make sure your `venv` is still activated), run:

```bash
python core/keygen.py

```

**What you should see:**
If successful, the terminal will print a "Success!" message followed by two 44-character Base64 encoded strings (your private and public keys).

**Validation Checklist:**

* [ ] Did the script run without crashing?
* [ ] Did it print two distinct keys?
* [ ] Look inside your `core/` folder. Ensure no `.key` or text files were created on your hard drive.

Run this test. If it works perfectly, reply with **"Phase 1 Validated"**, and I will provide the minute, step-by-step instructions for Phase 2: The YAML Policy Engine. If you hit any errors (like a `FileNotFoundError` or permission denied), paste the error here, and we will debug it before moving forward.