from fastapi import APIRouter, Request

from rems_co.models import ApproveEvent
from rems_co.service.rems_handlers import handle_approve, handle_revoke

router = APIRouter()


@router.post("/approve")
async def approve(request: Request) -> dict:
    data = await request.json()
    for item in data:
        try:
            event = ApproveEvent(**item)
            handle_approve(event)
        except Exception as e:
            print(f"[ERROR] Failed to process approve event {item}: {e}")
    return {"status": "ok"}


@router.post("/revoke")
async def revoke(request: Request) -> dict:
    data = await request.json()
    for item in data:
        try:
            event = ApproveEvent(**item)  # reuse same structure for now
            handle_revoke(event)
        except Exception as e:
            print(f"[ERROR] Failed to process revoke event {item}: {e}")
    return {"status": "ok"}
