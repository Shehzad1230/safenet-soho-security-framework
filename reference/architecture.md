
### 🏗️ The Hardened "Antigravity" Architecture

To ensure maximum performance without compromising on strict security, the entire architecture must be **Asynchronous**, **Authenticated**, and **Input-Sanitized**.

1. **The API Engine: FastAPI (TLS/HTTPS & Authenticated)**

* **Performance:** Built on Starlette and Pydantic, it is fully asynchronous and handles thousands of concurrent requests without blocking.
* **Security Upgrade:** * **HTTPS Enforcement:** The API must run over TLS (HTTPS). Transmitting WireGuard configurations (which contain private keys for mobile setup) over plain HTTP is a critical vulnerability.
* **API Key / JWT Auth:** No endpoint can be public. You will implement an API Key or JWT (JSON Web Token) dependency in FastAPI. Only your authenticated Flutter app or Typer CLI can issue commands.
* **Strict Interface Binding:** The API must **never** bind to `0.0.0.0` (all interfaces). Once the network is up, it should bind exclusively to `127.0.0.1` (localhost) or `10.0.0.1` (the SafeNet tunnel IP). This makes the API invisible to the physical Wi-Fi network .



2. **The CLI Backup: Typer**

* **Performance:** Uses standard Python type hints to build fast command-line interfaces instantly, replacing bloated libraries like `argparse` or `Click`.
* **Security Upgrade:** The CLI must interface directly with the core logic rather than bypassing the API's validation rules. Commands requiring elevated Windows permissions (like starting the tunnel) will trigger specific UAC (User Account Control) prompts rather than requiring the entire terminal to run as Administrator continuously.



3. **The Data Layer: aiosqlite + PyYAML (Secure Storage)**

* **Performance:** `policy.yml` is your "Source of Truth". You will use `aiosqlite` (async SQLite) with connection pooling to keep a high-speed, in-memory track of active connections. This eliminates slow disk-read bottlenecks when validating traffic.
* 
**Security Upgrade (The Golden Rule of Cryptography):** Your backend will generate the Public/Private key pair for mobile devices to create the QR code. However, the backend must **never save the client's Private Key to disk**. It holds it in memory, sends it to the Flutter app via HTTPS once, and immediately deletes it. The server's `policy.yml` and database only store the *Public Keys* of the peers.



4. **The Network Driver: `asyncio.subprocess` (Sanitized Executions)**

* **Performance:** To control WireGuard on Windows without freezing the API, your Python code will use async subprocesses to execute Windows command-line tools.
* **Security Upgrade (Anti-Injection):** You must never pass raw strings from the API directly to the command line. All inputs (like device names) must be strictly validated using Pydantic regex patterns to prevent **Command Injection attacks**. Subprocess calls must use list arguments (e.g., `["wg", "genkey"]`) rather than `shell=True`.

---

### 📂 The Secure Project Structure

Here is how you should structure your project directory to isolate sensitive components:

```text
safenet/
│
├── core/
│   ├── engine.py       # Async subprocess calls (Strictly sanitized)
│   ├── keygen.py       # Cryptographic generation (Memory-only private keys)
│   └── policy.py       # YAML parser with strict schema validation
│
├── api/
│   ├── main.py         # FastAPI application with TLS/HTTPS config
│   ├── routes.py       # API endpoints
│   ├── auth.py         # Security dependencies (API Key / JWT validation)
│   └── schemas.py      # Pydantic models for strict input validation
│
├── cli/
│   └── console.py      # Typer CLI application
│
├── data/               # Directory strictly permission-locked (OS-level)
│   ├── policy.yml      # Zero-Trust rules
│   └── safenet.db      # SQLite database (Stores Public Keys ONLY)
│
├── certs/              # SSL/TLS Certificates for HTTPS API
│   ├── server.crt
│   └── server.key
│
└── requirements.txt

```

---

### 🔌 The Protected API Endpoints (For Flutter & Web)

Your FastAPI backend (`api/routes.py`) serves as the bridge. Every endpoint here (except perhaps an initial login) must be protected by an authentication dependency.

* **`GET /api/network/status`** (Protected)
* Asynchronously checks if the WireGuard service is running via Windows APIs or lightweight subprocess checks.
* **`POST /api/network/toggle`** (Protected & Elevated)
* Turns the SafeNet tunnel on or off. Triggers `wireguard /installtunnelservice`.
* **`GET /api/devices/`** (Protected)
* Returns a JSON list of enrolled devices. *Sanitizes output to ensure no sensitive server keys leak.*
* **`POST /api/devices/enroll`** (Protected)
* **The Magic Endpoint:** Receives a device name. Validates the name against strict Regex. Generates the keys in memory. Assigns an IP, saves the *Public Key* to YAML, and returns the full configuration block (or Base64 QR code) to the Flutter frontend securely over HTTPS.


* **`POST /api/policy/update`** (Protected)
* Validates incoming schema using Pydantic. Updates the rules (e.g., blocking a specific phone) and triggers a fast, asynchronous network reload without dropping existing valid connections.



---

### ⌨️ The CLI Backup (Typer)

Because you wisely want a CLI backup, `Typer` makes this effortless. Your `cli/console.py` will look something like this:

```python
import typer
# import your core logic here

app = typer.Typer()

@app.command()
def start():
    """Starts the SafeNet WireGuard Tunnel on Windows"""
    typer.echo("🚀 Initiating Antigravity... Starting SafeNet Tunnel.")
    # Executes the secure engine logic
    
@app.command()
def add_device(name: str):
    """Enrolls a new device and generates its keys securely"""
    # Strict regex check on 'name' happens here before proceeding
    if not name.isalnum():
        typer.echo("⚠️ Security Error: Device name must be alphanumeric.")
        raise typer.Abort()
        
    typer.echo(f"Adding device: {name}...")
    # Call core keygen logic

if __name__ == "__main__":
    app()

```

---

### ⚙️ How to Control WireGuard on Windows via Python securely

Your Python `core/engine.py` will use `asyncio.create_subprocess_exec` to control the official Windows WireGuard executable.

1. **To Generate Keys:** You use the `wg.exe` tool to generate keys. Ensure the Python process captures the output standard streams (`stdout`) directly into memory variables, bypassing temporary files entirely to prevent disk-snooping.
2. **To Start the Network:** Python executes:
`["wireguard", "/installtunnelservice", "C:\\path\\to\\safenet.conf"]`. The config file generated here must have strict Windows file permissions so other apps cannot read the server's private key.
3. **To Stop the Network:**
`["wireguard", "/uninstalltunnelservice", "safenet"]`

### Your First Step:

Before you write any FastAPI or Flutter code, your **very first task** is to write a standalone, asynchronous Python script (`keygen.py`) that can generate a valid WireGuard public/private key pair using the `asyncio.subprocess` module, holding the private key entirely in memory.

Once you prove you can generate and discard keys securely without leaking them to disk, you have built the secure foundation of the Antigravity engine.