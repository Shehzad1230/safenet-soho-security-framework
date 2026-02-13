# Phase 2: The YAML Policy Parser & Database State

## Objective
To implement the "Declarative Security as Code" engine. We need to securely parse the user's `policy.yml` file, validate it strictly to prevent injection attacks, and store the network's state (Public Keys, IP Leases, and Group Assignments) in an asynchronous SQLite database.

## Security Constraints (Defense in Depth)
1. **Strict Input Validation:** We must never trust the YAML file blindly. All incoming data must be validated using **Pydantic** models. Device names must be strictly alphanumeric to prevent command injection when we pass them to the Windows shell later.
2. **No Private Keys on Disk:** The database will track `id`, `name`, `ip_address`, and `public_key`. It must **never** store the `private_key`.
3. **Async Database:** We must use `aiosqlite` to ensure database reads/writes do not block the main FastAPI event loop.

## The Policy Schema (`data/policy.yml`)
The user will define their network like this. The system assumes a "Default Deny" posture.

```yaml
devices:
  - name: worklaptop
    groups: [work, trusted]
  - name: smarttv
    groups: [iot, untrusted]

access_rules:
  - from: work
    to: trusted
    action: allow
```

Architectural Components
1. Database Layer (core/db.py)
Use aiosqlite to initialize a database at data/safenet.db.

Table devices: id (PK), name (Unique, String), public_key (String), ip_address (String).

Table groups: device_id (FK), group_name (String).

Functions needed: init_db(), add_device(), get_device().

2. Validation Layer (core/schemas.py)
Use Pydantic BaseModel.

Create models for DeviceNode, AccessRule, and SafeNetPolicy.

Apply Regex validators (e.g., ^[a-zA-Z0-9_-]+$) to the device names.

3. Policy Parser (core/policy.py)
Use yaml.safe_load() (NEVER yaml.load()) to read data/policy.yml.

Pass the raw dictionary into the Pydantic SafeNetPolicy model for validation.