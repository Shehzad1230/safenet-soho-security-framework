# Phase 4: The FastAPI Control Plane

## Objective
To expose the core WireGuard engine (`core/engine.py`), key generation (`core/keygen.py`), and SQLite state management (`core/db.py`) via a high-performance, asynchronous REST API. This API acts as the secure bridge between the Windows SafeNet gateway and the client devices connecting via the local Wi-Fi hotspot.

## Architectural Components

### 1. Authentication Layer (`api/auth.py`)
* **Security Posture:** The API must not be public. Even on a local hotspot, an attacker should not be able to trigger network changes.
* **Implementation:** Use FastAPI's `APIKeyHeader` dependency. Every protected endpoint must require an `X-API-Key` header. For the MVP, a static secure string (e.g., `safenet_dev_key_2026`) is acceptable.

### 2. Validation Layer (`api/schemas.py`)
* **Security Posture:** Strict input sanitization to prevent OS command injection when inputs are passed to the Windows shell.
* **Implementation:** Use Pydantic `BaseModel`. 
* **Key Schema:** `EnrollDeviceRequest` must require a `device_name`. Apply a strict Regex validator (e.g., `^[a-zA-Z0-9_-]{3,20}$`) to ensure no spaces or malicious shell characters are accepted.

### 3. Application Routes (`api/routes.py`)
* **Framework:** Use `APIRouter`. All endpoints must be `async def`.
* **Endpoints:**
  * `GET /api/status`: Returns `{"status": "active"}` or `{"status": "inactive"}` by checking if the adapter exists.
  * `POST /api/network/start`: Awaits `engine.start_safenet_tunnel()`.
  * `POST /api/network/stop`: Awaits `engine.stop_safenet_tunnel()`.
  * `POST /api/devices/enroll`: The core provisioning endpoint.
    1. Accepts `device_name`.
    2. Awaits `keygen.generate_wireguard_keys()` in-memory.
    3. Calculates an available `10.8.0.x` IP address.
    4. Saves the *Public Key* and IP to the SQLite database.
    5. Returns the complete WireGuard configuration (including the Private Key) as a JSON string for the client to consume (or convert to a QR code). **The private key is then immediately dropped from the server's memory.**

### 4. Application Main (`api/main.py`)
* Initialize `FastAPI()`.
* Include the `api/routes.py` router.
* Configure `CORSMiddleware` to allow `*` origins for local MVP testing (so the Flutter frontend can communicate with it).
* Bind the server to `0.0.0.0` during uvicorn startup so devices on the `192.168.137.x` Windows Hotspot can reach the API.