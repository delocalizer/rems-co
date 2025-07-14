from fastapi import FastAPI

from rems_co.listeners.events import router as event_router

app = FastAPI(
    title="REMS-COmanage Bridge",
    description="A service that syncs REMS entitlement notifications to COmanage.",
    version="1.0.0",
)

# Mount the event routes
app.include_router(event_router)


@app.get("/")
def healthcheck() -> dict:
    return {"status": "ok"}
