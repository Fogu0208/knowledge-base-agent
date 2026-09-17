"""聊天接口：POST /api/chat/stream，SSE 流式返回 Agent 全过程。"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agent import stream_answer

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    return StreamingResponse(
        stream_answer(req.session_id, req.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲，保证 token 实时到达
        },
    )
