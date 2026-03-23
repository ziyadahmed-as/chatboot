from dotenv import load_dotenv

load_dotenv(dotenv_path="env")  # loads arifgate_ai/env

from fastapi import FastAPI
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware

app = FastAPI(
    title="Role-Based AI Chatbot",
    description="Role-aware AI microservice for Course and Freelancing Marketplaces",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

from app.routers import ingest, chat, health
app.include_router(ingest.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")
app.include_router(health.router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Role-Based AI Chatbot Service"}
