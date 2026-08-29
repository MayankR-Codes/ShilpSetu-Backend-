"""
ShilpSetu — API Gateway
Entry point for the FastAPI application.
Mounts all service routers and configures middleware.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Load .env before anything else reads env vars

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api_gateway.logger import get_logger
from services.image_studio.main import image_router
from services.voice_cataloger.main import voice_router

logger = get_logger(__name__)

app = FastAPI(
    title="ShilpSetu AI Backend",
    description="AI/ML micro-services for the ShilpSetu artisan platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS (allow all origins for local dev — tighten in production) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files (serve uploaded/enhanced images) ──────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ────────────────────────────────────────────────────────
# NOTE: Auth is handled by Flutter — we do NOT manage login/tokens here
app.include_router(image_router, prefix="/api/v1/image", tags=["Image Studio"])
app.include_router(voice_router, prefix="/api/v1/catalog/voice", tags=["Voice Cataloger"])


# ── Health check ───────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    logger.info("Health check called")
    return {"status": "healthy", "version": "1.0.0"}


# ── Startup / shutdown events ──────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    logger.info("ShilpSetu API Gateway started")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("ShilpSetu API Gateway shutting down")
