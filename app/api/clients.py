"""
Dynamic Client Registration API (RFC 7591).

Endpoints for OAuth client registration and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas.oauth import DynamicClientInfo, DynamicClientRegister, DynamicClientResponse
from app.services.client_service import get_client, list_clients, register_client, revoke_client

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/register", response_model=DynamicClientResponse)
async def register_dynamic_client(
    request: DynamicClientRegister,
    db: AsyncSession = Depends(get_db),
) -> DynamicClientResponse:
    """
    Register new OAuth client (RFC 7591).

    Allows mobile and native applications to dynamically register
    as OAuth clients without pre-registration.

    Args:
        request: Client registration request
        db: Database session (injected)

    Returns:
        DynamicClientResponse with client credentials

    Example Request:
        {
            "platform": "ios",
            "redirect_uris": ["myapp://oauth/callback"]
        }

    Example Response:
        {
            "client_id": "client_abc123...",
            "client_secret": "secret_xyz789...",
            "platform": "ios",
            "redirect_uris": ["myapp://oauth/callback"],
            "expires_at": "2025-12-26T..."
        }

    Security Note:
        Client secret is returned ONCE and cannot be retrieved later.
        Store it securely on the client device.
    """
    # Validate platform
    valid_platforms = {"ios", "android", "macos", "windows", "linux", "cli"}
    if request.platform not in valid_platforms:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid platform. Must be one of: {', '.join(valid_platforms)}",
        )

    # Validate redirect URIs
    if not request.redirect_uris:
        raise HTTPException(
            status_code=400,
            detail="At least one redirect URI is required",
        )

    # Validate redirect URI format (basic validation)
    for uri in request.redirect_uris:
        if not uri.startswith(("http://", "https://", "myapp://", "app://")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid redirect URI format: {uri}",
            )

    # Register client (returns client + plain text secret)
    client, client_secret = await register_client(
        db,
        platform=request.platform,
        redirect_uris=request.redirect_uris,
        expires_in_days=365,
    )

    # Return client info with plain text secret
    return DynamicClientResponse(
        client_id=client.client_id,
        client_secret=client_secret,  # Use plain text secret from registration
        platform=client.platform,
        redirect_uris=client.redirect_uris,
        expires_at=client.expires_at,
    )


@router.get("/{client_id}", response_model=DynamicClientInfo)
async def get_client_info(
    client_id: str,
    db: AsyncSession = Depends(get_db),
) -> DynamicClientInfo:
    """
    Get client information (excludes secret).

    Args:
        client_id: Client ID
        db: Database session (injected)

    Returns:
        DynamicClientInfo without secret

    Raises:
        HTTPException: If client not found
    """
    client = await get_client(db, client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return DynamicClientInfo(
        client_id=client.client_id,
        platform=client.platform,
        redirect_uris=client.redirect_uris,
        created_at=client.created_at,
        expires_at=client.expires_at,
        last_used=client.last_used,
    )


@router.delete("/{client_id}")
async def revoke_client_registration(
    client_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Revoke client registration.

    Args:
        client_id: Client ID to revoke
        db: Database session (injected)

    Returns:
        Success message

    Raises:
        HTTPException: If client not found
    """
    revoked = await revoke_client(db, client_id)

    if not revoked:
        raise HTTPException(status_code=404, detail="Client not found")

    return {"message": "Client registration revoked"}


@router.get("/")
async def list_registered_clients(
    platform: str = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[DynamicClientInfo]]:
    """
    List registered clients.

    Args:
        platform: Optional platform filter
        db: Database session (injected)

    Returns:
        List of registered clients (excluding secrets)
    """
    clients = await list_clients(db, platform=platform)

    return {
        "clients": [
            DynamicClientInfo(
                client_id=client.client_id,
                platform=client.platform,
                redirect_uris=client.redirect_uris,
                created_at=client.created_at,
                expires_at=client.expires_at,
                last_used=client.last_used,
            )
            for client in clients
        ]
    }
