<div align="center">

# 🛡️ SafeNet SOHO Security Framework

**A Zero-Trust Micro-Perimeter Framework for Small Office/Home Office Environments**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![WireGuard](https://img.shields.io/badge/WireGuard-Latest-green.svg)](https://www.wireguard.com/)
[![License](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-2%20Complete-brightgreen.svg)](#project-status)

*Policy-driven, asynchronous, and hardened against injection attacks*

[Features](#-key-features) • [Architecture](#-architecture) • [Setup](#-quick-start) • [Documentation](#-documentation) • [Roadmap](#-development-roadmap)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Project Status](#-project-status)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Development Roadmap](#-development-roadmap)
- [Security](#-security)
- [Documentation](#-documentation)
- [License](#-license)

---

## 🌟 Overview

**Project SafeNet** is a lightweight, policy-driven Zero-Trust security framework designed for SOHO (Small Office/Home Office) environments. It leverages WireGuard to create an encrypted mesh network with declarative access control policies, all managed through a modern asynchronous Python backend.

### The Problem

Traditional home networks are **flat** and **permissive** — once a device connects to your Wi-Fi, it can access everything. IoT devices, smart TVs, and guests share the same network as your work laptop and private files.

### The Solution

SafeNet creates **micro-perimeters** around device groups with:
- 🔐 **Zero-Trust Architecture**: Default deny, explicit allow
- 📜 **Declarative Policies**: Define network rules in YAML
- 🚀 **WireGuard Mesh**: Encrypted peer-to-peer communication
- 🔒 **Memory-Only Keys**: Private keys never touch disk
- ⚡ **Fully Async**: Non-blocking I/O for maximum performance

---

## ✨ Key Features

### Implemented (Phases 1-2)

✅ **In-Memory Cryptography Engine**
- Async WireGuard key generation
- Zero-disk-key architecture
- Subprocess security (command injection prevention)

✅ **YAML Policy Parser**
- Declarative security-as-code
- Strict input validation via Pydantic
- Safe YAML loading (prevents code injection)

✅ **Async Database Layer**
- SQLite with `aiosqlite` for non-blocking I/O
- Parameterized queries (SQL injection prevention)
- Device and group management

### Coming Soon (Phases 3-5)

🔨 **WireGuard Subprocess Driver** (Phase 3)
- Tunnel lifecycle management (start/stop/status)
- Config file generation
- IP address assignment

🔨 **FastAPI Endpoints** (Phase 4)
- RESTful API with JWT authentication
- TLS/HTTPS enforcement
- Device enrollment and management

🔨 **Typer CLI Interface** (Phase 5)
- Command-line management tools
- Interactive setup wizard
- Status monitoring

---

## 📊 Project Status

| Phase | Component | Status | Tests |
|-------|-----------|--------|-------|
| **Phase 1** | In-Memory Cryptography | ✅ Complete | 4/4 Passing |
| **Phase 2** | Policy Parser & Database | ✅ Complete | 7/7 Passing |
| **Phase 3** | WireGuard Subprocess Driver | ✅ Complete + Live Tested | 9/9 Passing |
| **Phase 4** | FastAPI Endpoints | 🔨 In Progress | - |
| **Phase 5** | Typer CLI Interface | 📋 Planned | - |

**Current Version**: `0.3.0` (Phase 3 Complete - Network Validated)

---

## 🏗️ Architecture

### The "Antigravity" Security Model

SafeNet follows a hardened architecture with multiple defense layers:

```mermaid
graph TD
    A[YAML Policy File] -->|yaml.safe_load| B[Pydantic Validation]
    B -->|Strict Regex| C[Async Database]
    C -->|Parameterized Queries| D[SQLite State]
    E[WireGuard Keys] -->|Memory Only| F[Async Subprocess]
    F -->|No Shell Injection| G[wg.exe]
    B -->|Validated Config| H[WireGuard Mesh]
    D -->|Public Keys Only| H
```

### Security Principles

1. **Asynchronous-First**: Non-blocking I/O throughout
2. **Zero-Trust Cryptography**: Private keys never persist to disk
3. **Input Sanitization**: Regex validation prevents injection attacks
4. **Defense in Depth**: Multiple validation layers
5. **Fail-Secure**: Errors default to deny

### Data Flow

```
User Policy (YAML) 
    ↓
Pydantic Validation (Regex Checks)
    ↓
Async SQLite Database (Public Keys Only)
    ↓
WireGuard Config Generation
    ↓
Encrypted Mesh Network
```

---

## 🛠️ Tech Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Language** | Python 3.10+ | Async/await, type hints |
| **VPN** | WireGuard | Fast, modern VPN protocol |
| **Database** | SQLite + aiosqlite | Async state management |
| **Validation** | Pydantic v2 | Schema validation |
| **Config** | PyYAML | Policy parsing |
| **API** | FastAPI *(Phase 4)* | REST endpoints |
| **CLI** | Typer *(Phase 5)* | Command-line interface |

### Security Stack

- **Regex Validation**: `^[a-zA-Z0-9_-]{3,32}$` (prevents injection)
- **Parameterized Queries**: SQL injection prevention
- **yaml.safe_load**: Code injection prevention
- **subprocess.exec**: Command injection prevention

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
   ```powershell
   python --version
   ```

2. **WireGuard for Windows**
   - Download: https://www.wireguard.com/install/
   - Add to PATH: `C:\Program Files\WireGuard`

3. **Git** (for cloning)

### Installation

```powershell
# Clone the repository
git clone https://github.com/alvin-alvo/safenet-soho-security-framework.git
cd safenet-soho-security-framework

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```powershell
# Add WireGuard to PATH (if not already)
$env:Path += ";C:\Program Files\WireGuard"

# Run Phase 1 tests
python tests\test_phase1.py

# Run Phase 2 tests
python tests\test_phase2.py
```

Expected output:
```
Phase 1 Status: VALIDATED ✓
Phase 2 Status: VALIDATED ✓
```

---

## 🧪 Testing

### Run All Tests

```powershell
# All phases
python tests\run_all_tests.py

# Individual phases
python tests\test_phase1.py  # Cryptography engine
python tests\test_phase2.py  # Policy parser & database
```

### Test Coverage

- **Phase 1**: 4 tests (key generation, format, randomness, zero-disk)
- **Phase 2**: 7 tests (schema, YAML, database, SQL injection, etc.)

See [`tests/README.md`](tests/README.md) for detailed test documentation.

---

## 📂 Project Structure

```
safenet-soho-security-framework/
│
├── core/                   # Core framework components
│   ├── __init__.py        # Module exports
│   ├── keygen.py          # ✅ In-memory key generation (Phase 1)
│   ├── schemas.py         # ✅ Pydantic validation models (Phase 2)
│   ├── db.py              # ✅ Async SQLite database (Phase 2)
│   └── policy.py          # ✅ YAML policy parser (Phase 2)
│
├── api/                    # FastAPI endpoints (Phase 4)
│   └── __init__.py
│
├── cli/                    # Typer CLI interface (Phase 5)
│   └── __init__.py
│
├── data/                   # Runtime data and policies
│   ├── policy.yml         # ✅ Network policy configuration
│   └── safenet.db         # SQLite database (generated)
│
├── tests/                  # Test suite
│   ├── test_phase1.py     # ✅ Phase 1 validation tests
│   ├── test_phase2.py     # ✅ Phase 2 validation tests
│   ├── test_phase3.py     # Phase 3 tests (placeholder)
│   ├── run_all_tests.py   # Test runner
│   └── README.md          # Test documentation
│
├── docs/                   # Documentation
│   ├── phase1_validation_success.md
│   ├── phase2_validation_success.md
│   ├── phase2_complete.md
│   └── windows_setup_commands.md
│
├── reference/              # Design documents
│   ├── architecture.md    # "Antigravity" architecture
│   ├── phase1.md          # Phase 1 specifications
│   └── phase2.md          # Phase 2 specifications
│
├── certs/                  # TLS certificates (Phase 4)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 🗺️ Development Roadmap

### ✅ Phase 1: Environment Setup & In-Memory Cryptography (Complete)

- [x] Project structure initialization
- [x] Async WireGuard key generation
- [x] Zero-disk-key architecture
- [x] Comprehensive test suite
- [x] Documentation

**Validation**: 2026-02-13 | **Tests**: 4/4 Passing

---

### ✅ Phase 2: YAML Policy Parser & Database (Complete)

- [x] Pydantic validation schemas
- [x] Async SQLite database layer
- [x] YAML policy parser (yaml.safe_load)
- [x] SQL/Command injection prevention
- [x] Sample policy configuration
- [x] Comprehensive test suite

**Validation**: 2026-02-13 | **Tests**: 7/7 Passing

---

### 🔨 Phase 3: Windows WireGuard Subprocess Driver (In Progress)

- [ ] `core/engine.py` implementation
- [ ] WireGuard config file generation
- [ ] Tunnel lifecycle management (start/stop/status)
- [ ] IP address assignment logic
- [ ] Configuration validation
- [ ] Test suite

**Target**: TBD

---

### 📋 Phase 4: FastAPI Endpoints & JWT Authentication (Planned)

- [ ] FastAPI application setup
- [ ] Protected API endpoints
- [ ] JWT token authentication
- [ ] TLS/HTTPS configuration
- [ ] Device enrollment API
- [ ] Network management API

**Target**: TBD

---

### 📋 Phase 5: Typer CLI Interface (Planned)

- [ ] CLI command structure
- [ ] Device management commands
- [ ] Policy management commands
- [ ] Network control commands
- [ ] Interactive setup wizard
- [ ] Rich terminal output

**Target**: TBD

---

## 🔒 Security

### Attack Surface Mitigation

| Attack Vector | Mitigation |
|---------------|------------|
| **Command Injection** | Regex validation: `^[a-zA-Z0-9_-]{3,32}$` |
| **SQL Injection** | Parameterized queries only |
| **YAML Code Injection** | `yaml.safe_load` (no arbitrary code execution) |
| **Private Key Leakage** | Memory-only storage, never written to disk |
| **Man-in-the-Middle** | WireGuard encrypted tunnels + TLS API *(Phase 4)* |

### Security Testing

All phases include security-focused tests:
- Input validation (malicious device names)
- Injection attempt detection
- Cryptographic key security
- Zero-disk-key verification

See validation reports in [`docs/`](docs/) for detailed security analysis.

---

## 📚 Documentation

### User Documentation

- [Windows Setup Commands](docs/windows_setup_commands.md) - Installation guide
- [Test Documentation](tests/README.md) - Running tests
- [Phase 2 Complete](docs/phase2_complete.md) - Current status summary

### Implementation Documentation

- [Phase 1 Validation Report](docs/phase1_validation_success.md)
- [Phase 2 Validation Report](docs/phase2_validation_success.md)
- [Architecture Overview](reference/architecture.md) 
- [Phase 1 Specifications](reference/phase1.md)
- [Phase 2 Specifications](reference/phase2.md)

---

## 🤝 Contributing

Contributions are welcome! This project is licensed under GPL-3.0.

**To contribute:**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run all tests (`python tests/run_all_tests.py`)
5. Submit a pull request

Please ensure all security tests pass before submitting.

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

**Key Points:**
- ✅ Free to use, modify, and distribute
- ✅ Source code must remain open
- ✅ Derivative works must use GPL-3.0
- ❌ No warranty provided

---

## 🙏 Acknowledgments

- **WireGuard**: Modern, fast VPN protocol
- **FastAPI**: High-performance async web framework
- **Pydantic**: Data validation and settings management

---

<div align="center">

**Built with ❤️ for Zero-Trust SOHO Security**

[Report Bug](https://github.com/alvin-alvo/safenet-soho-security-framework/issues) • [Request Feature](https://github.com/alvin-alvo/safenet-soho-security-framework/issues)

</div>
