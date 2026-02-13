"""
SafeNet Phase 4 Tests - FastAPI Control Plane

This module tests the FastAPI REST API endpoints, JWT authentication,
input validation, and integration with the core modules.

Test Coverage:
- JWT token generation and validation
- API authentication (protected endpoints)
- Input validation (device name regex)
- Device enrollment endpoint
- Network management endpoints
- Status checking

Author: SafeNet Security Team
License: GPL-3.0
"""

# Set UTF-8 encoding for Windows console
import sys
import io
from pathlib import Path

# Add project root to path (allows running as script or module)
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
from typing import Dict, Optional

# HTTP client for testing FastAPI
from fastapi.testclient import TestClient

# SafeNet API
from api.main import app
from api.auth import create_access_token
from api.schemas import EnrollDeviceRequest


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST CLIENT SETUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

client = TestClient(app)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def get_auth_token() -> str:
    """
    Get a valid JWT token for testing protected endpoints.
    
    Returns:
        JWT token string
    """
    response = client.post(
        "/api/token",
        json={"username": "admin", "password": "safenet_admin_2026"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def get_auth_headers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Get authorization headers for API requests.
    
    Args:
        token: Optional JWT token (generates new one if not provided)
        
    Returns:
        Headers dictionary with Authorization Bearer token
    """
    if not token:
        token = get_auth_token()
    return {"Authorization": f"Bearer {token}"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: HEALTH CHECK (UNPROTECTED)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_health_check():
    """
    Test unprotected health check endpoint.
    
    Validates:
    - Endpoint is accessible without authentication
    - Returns correct status
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SafeNet API"
    print("[PASS] Test 1: Health check passed")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: JWT TOKEN GENERATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_jwt_token_generation():
    """
    Test JWT token generation with valid credentials.
    
    Validates:
    - Token is generated successfully
    - Token type is 'bearer'
    - Expiration time is set
    """
    response = client.post(
        "/api/token",
        json={"username": "admin", "password": "safenet_admin_2026"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 86400  # 24 hours in seconds
    print("[PASS] Test 2: JWT token generation passed")


def test_jwt_invalid_credentials():
    """
    Test JWT token generation with invalid credentials.
    
    Validates:
    - Returns 401 Unauthorized
    - Authentication fails gracefully
    """
    response = client.post(
        "/api/token",
        json={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401
    print("[PASS] Test 3: Invalid credentials rejected")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: AUTHENTICATION REQUIRED
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_protected_endpoint_without_auth():
    """
    Test that protected endpoints require authentication.
    
    Validates:
    - Returns 401 Unauthorized without token
    - Endpoints are properly secured
    """
    response = client.get("/api/status")
    assert response.status_code == 401  # Unauthorized (no auth provided)
    print("[PASS] Test 4: Protected endpoint requires authentication")


def test_protected_endpoint_with_auth():
    """
    Test that protected endpoints work with valid token.
    
    Validates:
    - Returns 200 OK with valid token
    - Authentication works correctly
    """
    headers = get_auth_headers()
    response = client.get("/api/status", headers=headers)
    assert response.status_code == 200
    print("[PASS] Test 5: Protected endpoint accessible with auth")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 6: INPUT VALIDATION (DEVICE NAME)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_valid_device_names():
    """
    Test device name validation with VALID names.
    
    Validates:
    - Alphanumeric names accepted
    - Dashes and underscores accepted
    - Regex validation works correctly
    """
    valid_names = [
        "laptop-01",
        "phone_alice",
        "iot-device-123",
        "MY_DEVICE",
        "test-123"
    ]
    
    for name in valid_names:
        # Validate using Pydantic model
        try:
            request = EnrollDeviceRequest(device_name=name)
            assert request.device_name == name
        except ValueError as e:
            raise AssertionError(f"Valid name '{name}' was rejected: {e}")
    
    print(f"[PASS] Test 6: Valid device names accepted ({len(valid_names)} tested)")


def test_invalid_device_names():
    """
    Test device name validation with INVALID names.
    
    Validates:
    - Spaces rejected
    - Special characters rejected
    - Path traversal rejected
    - Command injection prevented
    """
    invalid_names = [
        "my laptop",          # Space
        "device;rm-rf",       # Semicolon (command injection)
        "../../../etc",       # Path traversal
        "dev<script>",        # HTML/XSS
        "name!@#",            # Special chars
        "x" * 30,             # Too long (>20)
        "ab",                 # Too short (<3)
    ]
    
    for name in invalid_names:
        # Validate using Pydantic model
        try:
            request = EnrollDeviceRequest(device_name=name)
            raise AssertionError(f"Invalid name '{name}' was accepted (should be rejected)")
        except ValueError:
            pass  # Expected to fail
    
    print(f"[PASS] Test 7: Invalid device names rejected ({len(invalid_names)} tested)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 8: STATUS ENDPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_status_endpoint():
    """
    Test tunnel status endpoint.
    
    Validates:
    - Returns status information
    - Status is 'active' or 'inactive'
    """
    headers = get_auth_headers()
    response = client.get("/api/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["active", "inactive"]
    print(f"[PASS] Test 8: Status endpoint working (tunnel: {data['status']})")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 9: DEVICE ENROLLMENT (MOCKED)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_device_enrollment_validation():
    """
    Test device enrollment endpoint input validation.
    
    Validates:
    - Request validation works
    - Invalid names rejected at API level
    """
    headers = get_auth_headers()
    
    # Test with invalid name
    response = client.post(
        "/api/devices/enroll",
        headers=headers,
        json={"device_name": "invalid name!"}  # Space and special char
    )
    assert response.status_code == 422  # Validation error
    print("[PASS] Test 9: Device enrollment validates input")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST RUNNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def run_all_tests():
    """
    Run all Phase 4 tests.
    
    Returns:
        True if all tests pass, False otherwise
    """
    print()
    print("=" * 70)
    print("SafeNet Phase 4 Tests - FastAPI Control Plane")
    print("=" * 70)
    print()
    
    tests = [
        ("Health Check", test_health_check),
        ("JWT Token Generation", test_jwt_token_generation),
        ("Invalid Credentials", test_jwt_invalid_credentials),
        ("Authentication Required", test_protected_endpoint_without_auth),
        ("Authentication Success", test_protected_endpoint_with_auth),
        ("Valid Device Names", test_valid_device_names),
        ("Invalid Device Names", test_invalid_device_names),
        ("Status Endpoint", test_status_endpoint),
        ("Device Enrollment Validation", test_device_enrollment_validation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] Test failed: {name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] Test error: {name}")
            print(f"   Error: {e}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Phase 4 Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    print()
    
    if failed == 0:
        print("[PASS] Phase 4 Status: VALIDATED")
        return True
    else:
        print("[FAIL] Phase 4 Status: FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
