from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401
from core.database import AsyncSessionLocal, Base, engine
from routers.channels import router as channels_router
from routers.messages import router as messages_router
from routers.notifications import router as notifications_router
from routers.users import router as users_router
from services.realtime import manager
from services.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_if_empty(session)
    yield


app = FastAPI(
    title="Bards API",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[{"name": "channels"}, {"name": "messages"}],
    swagger_ui_parameters={"persistAuthorization": True},
    components={
        "securitySchemes": {
            "DemoUserId": {
                "type": "apiKey",
                "in": "header",
                "name": "x-user-id",
            }
        }
    },
    security=[{"DemoUserId": []}],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(channels_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    channel_id: str = Query(...),
    user_id: str = Query(...),
):
    await manager.connect(ws, channel_id, user_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws, channel_id, user_id)
