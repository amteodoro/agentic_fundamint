from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import stocks, analysis, criteria, chat, auth, portfolio, watchlist
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup: Initialize database
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")
    
    yield
    
    # Shutdown: Close database connections
    print("Closing database connections...")
    await close_db()
    print("Database connections closed.")


app = FastAPI(
    title="Fundamint API",
    description="API for the Fundamint stock analysis platform with user authentication and portfolio management.",
    version="0.2.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:3100",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing routers
app.include_router(stocks.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(criteria.router, prefix="/api")
app.include_router(chat.router, prefix="/api/chat")

# New authentication and user data routers
app.include_router(auth.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")


@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Welcome to the Fundamint API!"}


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "0.2.0"}

