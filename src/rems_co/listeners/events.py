from fastapi import APIRouter

from rems_co.models import ApproveEvent, RevokeEvent
from rems_co.service.rems_handlers import handle_approve, handle_revoke

router = APIRouter()


@router.post("/approve")
async def approve(events: list[ApproveEvent]) -> dict:
    for event in events:
        try:
            handle_approve(event)
        except Exception as e:
            print(f"[ERROR] Failed to process approve event {event}: {e}")
    return {"status": "ok"}


@router.post("/revoke")
async def revoke(events: list[RevokeEvent]) -> dict:
    for event in events:
        try:
            handle_revoke(event)
        except Exception as e:
            print(f"[ERROR] Failed to process revoke event {event}: {e}")
    return {"status": "ok"}
