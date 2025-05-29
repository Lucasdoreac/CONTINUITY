from fastapi import FastAPI
from contextlib import asynccontextmanager

# Adjust import path based on actual project structure
# If main.py and database.py are in the same 'core' directory:
from .database import create_db_and_tables, SessionLocal # Added SessionLocal for potential future use
from .models import Projeto, Usuario, Sessao # For potential future use with routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    print("INFO:     Starting up MCP Continuity Service...")
    print("INFO:     Creating database tables if they don't exist...")
    create_db_and_tables()
    print("INFO:     Database tables checked/created.")
    yield
    # Code to run on shutdown (if any)
    print("INFO:     Shutting down MCP Continuity Service...")

app = FastAPI(
    title="MCP Continuity Service",
    version="0.1.0",
    description="Service for managing Continuity of Operations Plans (COOPs).",
    lifespan=lifespan
)

@app.get("/health", tags=["General"])
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok", "message": "Service is healthy"}

# Include routers for different resources
from .routers import users as users_router
from .routers import projects as projects_router # Import the projects router

# app.include_router(projetos_router, prefix="/api/v1") # Example for other routers
app.include_router(users_router.router, prefix="/api/v1") 
app.include_router(projects_router.router, prefix="/api/v1")
from .routers import sessions as sessions_router
app.include_router(sessions_router.router, prefix="/api/v1") 
from .routers import websockets as websockets_router # Import the websockets router
app.include_router(websockets_router.router) # WebSocket router might not need a prefix like /api/v1

# To run this app (from the project root directory, assuming uvicorn is installed):
# uvicorn mcp_continuity_service.core.main:app --reload --port 8000
# Or, if you are inside the 'mcp_continuity_service' directory:
# uvicorn core.main:app --reload --port 8000

# Placeholder for root endpoint
@app.get("/", tags=["General"])
async def read_root():
    """
    Root endpoint providing basic information about the API.
    """
    return {
        "message": "Welcome to the MCP Continuity Service API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/health"
    }
