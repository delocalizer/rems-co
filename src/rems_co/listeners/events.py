"""
HTTP routes for receiving REMS entitlement events and triggering business logic.
"""

import logging

from fastapi import APIRouter

from rems_co.models import ApproveEvent, RevokeEvent
from rems_co.service.rems_handlers import handle_approve, handle_revoke

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/approve")
async def approve(events: list[ApproveEvent]) -> dict:
    """Handle a batch of REMS approval events."""
    for event in events:
        try:
            handle_approve(event)
        except Exception as e:
            logger.error(f"Failed to process approve event {event}: {e}", exc_info=True)
    return {"status": "ok"}


@router.post("/revoke")
async def revoke(events: list[RevokeEvent]) -> dict:
    """Handle a batch of REMS revocation events."""
    for event in events:
        try:
            handle_revoke(event)
        except Exception as e:
            logger.error(f"Failed to process revoke event {event}: {e}", exc_info=True)
    return {"status": "ok"}
