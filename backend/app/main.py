from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import stocks, analysis, criteria, chat

app = FastAPI(
    title="Fundamint API",
    description="API for the Fundamint stock analysis platform.",
    version="0.1.0",
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

app.include_router(stocks.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(criteria.router, prefix="/api")
app.include_router(chat.router, prefix="/api/chat")

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Welcome to the Fundamint API!"}
