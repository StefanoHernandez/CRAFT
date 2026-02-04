
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from craft.api.websocket import manager, broadcast_agent_events
from craft.api.events import get_global_emitter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.hub")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    emitter = get_global_emitter()
    # Start event broadcaster in background
    import asyncio
    asyncio.create_task(broadcast_agent_events(emitter))
    
    logger.info("🚀 CRAFT Nexus Integrated Server Ready")
    yield
    # Shutdown logic if needed

def create_app() -> FastAPI:
    app = FastAPI(title="CRAFT Nexus Integrated Hub", lifespan=lifespan)

    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
