"""全局配置：所有可变参数集中在这里，从 backend/.env 读取。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # LLM（OpenAI 兼容协议，可切 OpenAI / DeepSeek / SiliconFlow / 通义 等）
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "sk-placeholder")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Embedding 模型（可以和 LLM 用不同服务商）
    EMBEDDING_BASE_URL: str = os.getenv("EMBEDDING_BASE_URL") or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY") or os.getenv("LLM_API_KEY", "sk-placeholder")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Milvus 向量库
    MILVUS_URI: str = os.getenv("MILVUS_URI", "http://localhost:19530")
    MILVUS_COLLECTION: str = os.getenv("MILVUS_COLLECTION", "knowledge_base")

    # 本地数据：SQLite 元数据 + 上传文件
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    APP_DB_PATH: Path = DATA_DIR / "app.db"


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
