from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
load_dotenv(dotenv_path="env")  # backward compat

from fastapi import FastAPI
from app.middleware.auth import AuthMiddleware
from app.middleware.logging import LoggingMiddleware
from app.routers import chat, health, generate, recommend, ingest

app = FastAPI(
    title="Arifgate AI",
    description="Role-aware RAG chatbot, content generation, recommendations & matching — powered by LangChain + ChromaDB + OpenAI",
    version="3.0.0",
)

app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(chat.router, prefix="/v1")
app.include_router(generate.router, prefix="/v1")
app.include_router(recommend.router, prefix="/v1")
app.include_router(ingest.router, prefix="/v1")
app.include_router(health.router, prefix="/v1")


@app.get("/")
async def root():
    return {"message": "Arifgate AI Service v3 — visit /docs"}
