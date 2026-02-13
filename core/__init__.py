"""
SafeNet Core Module

This module provides the foundational cryptographic and network management
components for the SafeNet Zero-Trust micro-perimeter framework.

Components:
- keygen: Secure, in-memory WireGuard key generation

Security Architecture: "Antigravity"
- Zero-disk-key cryptography
- Fully asynchronous subprocess execution
- Strict input sanitization
- TLS/HTTPS enforced communications
"""

__version__ = "0.1.0"
__author__ = "SafeNet Development Team"

# Import key generation function for module-level access
from .keygen import generate_wireguard_keys

__all__ = ["generate_wireguard_keys"]
