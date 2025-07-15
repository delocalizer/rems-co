"""
Entrypoint for the REMS-COmanage bridge FastAPI application.
Sets up routes and provides a basic healthcheck.
"""

import logging

from fastapi import FastAPI

from rems_co import __version__
from rems_co.listeners.events import router as event_router

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

app = FastAPI(
    title="REMS-COmanage Bridge",
    description="A service that syncs REMS entitlement notifications to COmanage.",
    version=__version__,
)

# Register endpoints for /approve and /revoke
app.include_router(event_router)


@app.get("/")
def healthcheck() -> dict:
    """Basic health check endpoint."""
    return {"status": "ok"}
