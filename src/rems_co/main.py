"""
Entrypoint for the REMS-COmanage bridge FastAPI application.
Sets up routes and provides a basic healthcheck.
"""

from fastapi import FastAPI

from rems_co.listeners.events import router as event_router

app = FastAPI(
    title="REMS-COmanage Bridge",
    description="A service that syncs REMS entitlement notifications to COmanage.",
    version="1.0.0",
)

# Register endpoints for /approve and /revoke
app.include_router(event_router)


@app.get("/")
def healthcheck() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}
