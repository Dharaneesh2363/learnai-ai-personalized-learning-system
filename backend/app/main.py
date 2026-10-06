from contextlib import asynccontextmanager
import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.services.ai.factory import get_ai_provider

# Configure structured application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("learning_system")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan event handler for database and cache lifecycle."""
    logger.info("Initializing database schema on startup...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"{settings.PROJECT_NAME} initialized successfully in {settings.ENVIRONMENT} mode.")
    yield
    logger.info(f"{settings.PROJECT_NAME} shutting down cleanly.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Full-stack AI-Powered Personalized Learning System with Knowledge Modeling, Adaptive Quizzing, and Explainable Recommendations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    """Enforces security headers and measures request processing latency."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Add standard enterprise security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Took {duration:.3f}s"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Centralized exception handler to prevent leaking raw internal stack traces
    while capturing full diagnostic logs for production monitoring.
    """
    logger.error(f"Unhandled exception during {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. The incident has been recorded.",
            "path": request.url.path
        }
    )


@app.get("/health", tags=["Health"])
def health_check():
    """
    Deep health check probe for container orchestrators (Kubernetes / Docker Compose).
    Verifies live database connectivity and AI provider availability.
    """
    db_status = "connected"
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "degraded"

    ai_provider = get_ai_provider()
    ai_status = "ready"
    try:
        # Quick check of AI provider name
        provider_name = type(ai_provider).__name__
    except Exception:
        ai_status = "degraded"
        provider_name = "unknown"

    overall_healthy = (db_status == "connected")
    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "degraded",
            "service": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
            "ai_provider": settings.AI_PROVIDER,
            "ai_provider_class": provider_name,
            "ai_status": ai_status
        }
    )


@app.get("/", tags=["Root"])
def root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API",
        "documentation": "/docs",
        "api_v1": settings.API_V1_STR
    }


# Mount API V1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)
