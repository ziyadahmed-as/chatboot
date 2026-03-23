from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
load_dotenv(dotenv_path="env")  # backward compat

from fastapi import FastAPI
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.routers import chat, health

app = FastAPI(
    title="Arifgate AI Chatbot",
    description="Role-aware AI chatbot for Course and Freelancing Marketplaces",
    version="1.0.0",
)

app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(chat.router, prefix="/v1")
app.include_router(health.router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Arifgate AI Chatbot — visit /docs"}
