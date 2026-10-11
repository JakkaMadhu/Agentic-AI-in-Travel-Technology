from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables and resources."""
    try:
        init_db()
    except Exception as e:
        print(f"[Database Init Warning]: Could not connect to PostgreSQL: {e}")
    yield
    if not db.is_closed():
        db.close()

app = FastAPI(
    title="AgenticTravelTech Backend",
    version="1.0.0",
    description="Agentic travel planning backend service with FastAPI, Peewee, PostgreSQL, and LangGraph",
    lifespan=lifespan
)

from app.config import settings

# Configure CORS for client and deployment integrations
raw_origins = getattr(settings, "CORS_ORIGINS", "*").strip()
if raw_origins == "*" or not raw_origins:
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Service health and database status probe."""
    db_connected = not db.is_closed()
    return {
        "status": "healthy",
        "database_connected": db_connected
    }

# Register route modules
from app.routes.auth import router as auth_router
from app.routes.trip import router as trip_router

app.include_router(auth_router)
app.include_router(trip_router)
