"""
SafeNet API - Route Definitions

This module defines all API endpoints for the SafeNet control plane.
All endpoints are protected with JWT authentication and use async execution.

Endpoints:
- POST /api/token - Generate JWT authentication token
- GET /api/status - Check WireGuard tunnel status
- POST /api/network/start - Start WireGuard tunnel
- POST /api/network/stop - Stop WireGuard tunnel  
- POST /api/devices/enroll - Enroll new device and generate config

Security:
- All endpoints require JWT authentication (except /token)
- Strict input validation via Pydantic
- Async/await for non-blocking execution
- No shell=True (prevents command injection)

Author: SafeNet Security Team
License: GPL-3.0
"""

import logging
from typing import Dict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

# SafeNet core modules
from core import (
    generate_wireguard_keys,
    generate_config_string,
    start_safenet_tunnel,
    stop_safenet_tunnel,
    get_tunnel_status,
    add_device,
    get_device,
    init_db
)

# API modules
from api.auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_HOURS
from api.schemas import (
    TokenRequest,
    TokenResponse,
    EnrollDeviceRequest,
    EnrollDeviceResponse,
    StatusResponse,
    NetworkResponse,
    ErrorResponse
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Logger
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api", tags=["safenet"])

# Hardcoded credentials for MVP (replace with database in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "safenet_admin_2026"  # TODO: Use environment variable


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTICATION ENDPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Generate JWT Token",
    description="Authenticate and receive a JWT token for API access"
)
async def login(request: TokenRequest) -> TokenResponse:
    """
    Generate JWT authentication token.
    
    For MVP, uses hardcoded admin credentials.
    In production, integrate with proper user database.
    
    Args:
        request: Username and password
        
    Returns:
        JWT token with expiration time
        
    Raises:
        HTTPException 401: Invalid credentials
    """
    logger.info(f"Login attempt for user: {request.username}")
    
    # Validate credentials (hardcoded for MVP)
    if request.username != ADMIN_USERNAME or request.password != ADMIN_PASSWORD:
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": request.username, "role": "admin"},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )
    
    logger.info(f"JWT token generated for user: {request.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600  # Convert to seconds
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TUNNEL STATUS ENDPOINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Check Tunnel Status",
    description="Check if the WireGuard tunnel is active"
)
async def check_status(
    current_user: Dict = Depends(get_current_user)
) -> StatusResponse:
    """
    Check WireGuard tunnel status.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        Status response with tunnel state
        
    Security:
        Requires valid JWT token
    """
    logger.info(f"Status check requested by: {current_user['sub']}")
    
    try:
        # Query tunnel status from Windows service
        status_info = await get_tunnel_status()
        
        if status_info and status_info.get("state") == "4":
            # State 4 = RUNNING
            return StatusResponse(
                status="active",
                service_state=status_info.get("state"),
                message="Tunnel is running"
            )
        else:
            return StatusResponse(
                status="inactive",
                service_state=status_info.get("state") if status_info else None,
                message="Tunnel is not running"
            )
            
    except Exception as e:
        logger.error(f"Error checking tunnel status: {e}")
        return StatusResponse(
            status="inactive",
            message=f"Error checking status: {str(e)}"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NETWORK MANAGEMENT ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/network/start",
    response_model=NetworkResponse,
    summary="Start Tunnel",
    description="Start the WireGuard tunnel (requires admin privileges)"
)
async def start_tunnel(
    current_user: Dict = Depends(get_current_user)
) -> NetworkResponse:
    """
    Start the WireGuard tunnel.
    
    Requires Windows administrator privileges.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        Network operation response
        
    Raises:
        HTTPException 500: If tunnel start fails
        
    Security:
        Requires valid JWT token and admin privileges
    """
    logger.info(f"Tunnel start requested by: {current_user['sub']}")
    
    try:
        # Generate config from database (will need peer list)
        # For now, start with empty config
        config = generate_config_string(
            private_key="dummy_key",  # Will be replaced with actual server key
            local_ip="10.8.0.1/24",
            peers=[]
        )
        
        # Start the tunnel
        success = await start_safenet_tunnel(config)
        
        if success:
            logger.info("Tunnel started successfully")
            return NetworkResponse(
                success=True,
                message="Tunnel started successfully",
                operation="start"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start tunnel"
            )
            
    except Exception as e:
        logger.error(f"Error starting tunnel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tunnel start failed: {str(e)}"
        )


@router.post(
    "/network/stop",
    response_model=NetworkResponse,
    summary="Stop Tunnel",
    description="Stop the WireGuard tunnel"
)
async def stop_tunnel(
    current_user: Dict = Depends(get_current_user)
) -> NetworkResponse:
    """
    Stop the WireGuard tunnel.
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        Network operation response
        
    Security:
        Requires valid JWT token
    """
    logger.info(f"Tunnel stop requested by: {current_user['sub']}")
    
    try:
        # Stop the tunnel
        success = await stop_safenet_tunnel()
        
        if success:
            logger.info("Tunnel stopped successfully")
            return NetworkResponse(
                success=True,
                message="Tunnel stopped successfully",
                operation="stop"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to stop tunnel"
            )
            
    except Exception as e:
        logger.error(f"Error stopping tunnel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tunnel stop failed: {str(e)}"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEVICE ENROLLMENT ENDPOINT (CORE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post(
    "/devices/enroll",
    response_model=EnrollDeviceResponse,
    summary="Enroll Device",
    description="Generate WireGuard keys and configuration for a new device"
)
async def enroll_device(
    request: EnrollDeviceRequest,
    current_user: Dict = Depends(get_current_user)
) -> EnrollDeviceResponse:
    """
    Enroll a new device in the SafeNet network.
    
    This is the CORE provisioning endpoint. It:
    1. Validates device name (via Pydantic)
    2. Generates WireGuard keys in-memory
    3. Assigns an available IP address
    4. Saves public key + IP to database
    5. Returns complete config (including private key)
    6. Private key is immediately dropped from memory
    
    Args:
        request: Device enrollment request with device_name
        current_user: Authenticated user from JWT token
        
    Returns:
        Complete WireGuard configuration for the client
        
    Raises:
        HTTPException 409: Device already exists
        HTTPException 500: Enrollment failed
        
    Security:
        - Device name validated by Pydantic (prevents injection)
        - Private key never stored (ephemeral)
        - JWT authentication required
    """
    logger.info(f"Device enrollment requested by {current_user['sub']}: {request.device_name}")
    
    try:
        # Initialize database
        await init_db()
        
        # Check if device already exists
        existing_device = await get_device(request.device_name)
        if existing_device:
            logger.warning(f"Device already exists: {request.device_name}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Device '{request.device_name}' already exists"
            )
        
        # Generate WireGuard keys (in-memory only)
        logger.info(f"Generating WireGuard keys for: {request.device_name}")
        private_key, public_key = await generate_wireguard_keys()
        
        # Assign IP address (simple incrementing for MVP)
        # TODO: Implement proper IP pool management
        assigned_ip = "10.8.0.2/24"  # For MVP, hardcode first client IP
        
        # Save device to database (public key only)
        logger.info(f"Saving device to database: {request.device_name}")
        await add_device(
            name=request.device_name,
            public_key=public_key,
            ip_address=assigned_ip.split("/")[0],  # Store without CIDR
            group="default"
        )
        
        # Generate WireGuard configuration string
        config = generate_config_string(
            private_key=private_key,
            local_ip=assigned_ip,
            peers=[]  # For MVP, no peers yet
        )
        
        logger.info(f"Device enrolled successfully: {request.device_name}")
        
        # Return complete configuration
        # Private key is included HERE ONLY and never stored
        return EnrollDeviceResponse(
            device_name=request.device_name,
            assigned_ip=assigned_ip,
            public_key=public_key,
            private_key=private_key,  # EPHEMERAL - client must save!
            config_string=config
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 409 Conflict)
        raise
        
    except Exception as e:
        logger.error(f"Device enrollment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrollment failed: {str(e)}"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEALTH CHECK (UNPROTECTED)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.get(
    "/health",
    summary="Health Check",
    description="Unprotected health check endpoint"
)
async def health_check():
    """
    Simple health check endpoint (no authentication required).
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "SafeNet API"}
