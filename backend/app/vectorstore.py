"""Milvus 向量库连接：懒加载单例。

只在真正用到（检索 / 入库）时才连接，
所以后端没起 Milvus 也能正常启动、正常用联网搜索和 SQL 工具。
"""
from functools import lru_cache

from langchain_milvus import Milvus

from app.config import settings
from app.llm import get_embeddings


@lru_cache(maxsize=1)
def get_vectorstore() -> Milvus:
    return Milvus(
        embedding_function=get_embeddings(),
        connection_args={"uri": settings.MILVUS_URI},
        collection_name=settings.MILVUS_COLLECTION,
        auto_id=True,          # 主键自增
        index_params={"index_type": "FLAT", "metric_type": "COSINE"},
    )
