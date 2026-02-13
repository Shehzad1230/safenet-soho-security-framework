# SafeNet Test Suite

This directory contains all validation tests for the SafeNet SOHO Security Framework.

## Running Tests

### Individual Phase Tests

```powershell
# Phase 1: In-Memory Cryptography Engine
python tests\test_phase1.py

# Phase 2: YAML Policy Parser & Database
python tests\test_phase2.py

# Phase 3: WireGuard Subprocess Driver (not yet implemented)
python tests\test_phase3.py
```

### Phase 3 Tests

**File**: `test_phase3.py`

**Purpose**: Validates Windows WireGuard subprocess driver implementation

**Test Coverage**:
- WireGuard config generation (INI format)
- Multi-peer configuration support
- Windows absolute path resolution
- Command injection prevention (no `shell=True`)
- List-based subprocess arguments
- Async subprocess execution
- Tunnel lifecycle (skipped if not admin)

**Run Command**:
```powershell
python tests\test_phase3.py
```

**Manual Tunnel Test** (Requires Admin):
```powershell
python tests\test_tunnel_manual.py
```

This script performs full tunnel lifecycle testing:
- Generates fresh WireGuard keys
- Creates tunnel configuration 
- Starts tunnel (installs Windows service)
- Checks tunnel status
- Stops tunnel (removes Windows service)
- Verifies cleanup

**Live Network Validation Test** (Recommended - Requires Admin):
```powershell
python tests\test_engine.py
```

**PROVEN WORKING** [COMPLETE] - This script:
- Creates a REAL WireGuard tunnel on Windows
- Holds it open for 30 seconds
- Instructions to verify with `ipconfig` (look for IP 10.8.0.1)
- Automatically cleans up
- **Validates Python control of Windows network stack**

See [TESTING.md](../TESTING.md) for detailed testing guide.

### Run All Tests

```powershell
python tests\run_all_tests.py
```

## Test Coverage

### Phase 1: In-Memory Cryptography Engine [COMPLETE]
- [x] Async key generation via `asyncio.subprocess`
- [x] WireGuard key format validation (44-char Base64)
- [x] Cryptographic randomness verification
- [x] Zero-disk-key architecture validation

**Status**: [COMPLETE] PASSING

### Phase 2: YAML Policy Parser & Database [COMPLETE]
- [x] Pydantic schema validation
- [x] YAML policy parser (`yaml.safe_load`)
- [x] Async SQLite database (aiosqlite)
- [x] SQL injection protection
- [x] Command injection protection (device name validation)
- [x] Foreign key constraints
- [x] Group membership queries

**Status**: [COMPLETE] PASSING

### Phase 3: WireGuard Subprocess Driver [IN PROGRESS]
- [ ] WireGuard config file generation
- [ ] Tunnel lifecycle management
- [ ] IP address assignment
- [ ] Configuration validation

**Status**: [IN PROGRESS] NOT YET IMPLEMENTED

### Phase 4: FastAPI Endpoints & Authentication [IN PROGRESS]
**Status**: [IN PROGRESS] NOT YET IMPLEMENTED

### Phase 5: Typer CLI Interface [IN PROGRESS]
**Status**: [IN PROGRESS] NOT YET IMPLEMENTED

## Test Organization

```
tests/
├── __init__.py # Test package initialization
├── test_phase1.py # Phase 1 validation tests
├── test_phase2.py # Phase 2 validation tests
├── test_phase3.py # Phase 3 validation tests (placeholder)
└── run_all_tests.py # Test runner for all phases
```

## Requirements

All tests require the project dependencies to be installed:

```powershell
pip install -r requirements.txt
```

Phase 1 tests additionally require:
- WireGuard for Windows installed
- `wg.exe` in system PATH

## Expected Output

All tests should print validation results with `[PASS]` or `[FAIL]` markers.

Successful test completion shows:
```
Phase X Status: VALIDATED
```

Failed tests will print error details and exit with code 1.
