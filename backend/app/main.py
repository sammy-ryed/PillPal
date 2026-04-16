"""
PillPal FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health, prescriptions
from app.services.medicine_corrector import MedicineCorrector
from app.services.frequency_parser import FrequencyParser
from app.services.supabase_service import SupabaseService, set_supabase_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PillPal API starting up…")

    svc = SupabaseService(settings)
    await svc.initialize()
    set_supabase_service(svc)

    MedicineCorrector.initialize(svc)
    FrequencyParser.initialize(svc)

    logger.info("PillPal API ready.")
    yield
    logger.info("PillPal API shutting down.")


app = FastAPI(
    title="PillPal API",
    version="1.0.0",
    description="Prescription OCR intelligence pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(prescriptions.router, prefix="/api/prescriptions")
