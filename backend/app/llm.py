"""LLM 与 Embedding 客户端：lru_cache 保证全局单例。"""
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        streaming=True,  # 打开流式，前端才能逐 token 显示
        temperature=0.2,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.EMBEDDING_API_KEY,
        base_url=settings.EMBEDDING_BASE_URL,
    )
