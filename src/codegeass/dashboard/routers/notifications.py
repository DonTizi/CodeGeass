"""Notifications API router."""

from fastapi import APIRouter, HTTPException, Query

from ..dependencies import get_notification_service
from ..models import (
    Channel,
    ChannelCreate,
    ChannelUpdate,
    ProviderInfo,
    TestResult,
)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/channels", response_model=list[Channel])
async def list_channels(
    enabled_only: bool = Query(False, description="Return only enabled channels"),
):
    """List all notification channels."""
    service = get_notification_service()
    channels = service.list_channels()
    if enabled_only:
        channels = [ch for ch in channels if ch.enabled]
    return channels


@router.get("/channels/{channel_id}", response_model=Channel)
async def get_channel(channel_id: str):
    """Get a channel by ID."""
    service = get_notification_service()
    channel = service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.post("/channels", response_model=Channel, status_code=201)
async def create_channel(data: ChannelCreate):
    """Create a new notification channel."""
    service = get_notification_service()
    try:
        return service.create_channel(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/channels/{channel_id}", response_model=Channel)
async def update_channel(channel_id: str, data: ChannelUpdate):
    """Update a channel."""
    service = get_notification_service()
    channel = service.update_channel(channel_id, data)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.delete("/channels/{channel_id}")
async def delete_channel(
    channel_id: str,
    delete_credentials: bool = Query(True, description="Also delete credentials"),
):
    """Delete a notification channel."""
    service = get_notification_service()
    if not service.delete_channel(channel_id, delete_credentials):
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"status": "success", "message": f"Channel {channel_id} deleted"}


@router.post("/channels/{channel_id}/enable")
async def enable_channel(channel_id: str):
    """Enable a notification channel."""
    service = get_notification_service()
    if not service.enable_channel(channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"status": "success", "message": f"Channel {channel_id} enabled"}


@router.post("/channels/{channel_id}/disable")
async def disable_channel(channel_id: str):
    """Disable a notification channel."""
    service = get_notification_service()
    if not service.disable_channel(channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    return {"status": "success", "message": f"Channel {channel_id} disabled"}


@router.post("/channels/{channel_id}/test", response_model=TestResult)
async def test_channel(channel_id: str):
    """Test a notification channel connection."""
    service = get_notification_service()
    channel = service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    return await service.test_channel(channel_id)


@router.post("/channels/{channel_id}/send-test")
async def send_test_message(
    channel_id: str,
    message: str = Query("Test notification from CodeGeass!", description="Test message"),
):
    """Send a test message to a channel."""
    service = get_notification_service()
    channel = service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    success = await service.send_test_message(channel_id, message)
    if success:
        return {"status": "success", "message": "Test message sent"}
    raise HTTPException(status_code=500, detail="Failed to send test message")


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    """List available notification providers with their configuration schemas."""
    service = get_notification_service()
    return service.list_providers()


@router.get("/providers/{provider_name}", response_model=ProviderInfo)
async def get_provider(provider_name: str):
    """Get information about a specific provider."""
    service = get_notification_service()
    provider = service.get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider
