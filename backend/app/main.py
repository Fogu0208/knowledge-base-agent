"""FastAPI 入口：uvicorn app.main:app --reload 启动。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routers import chat, documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # 建表 + 灌入演示业务数据
    yield


app = FastAPI(title="知识库 Agent 助手", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(documents.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
