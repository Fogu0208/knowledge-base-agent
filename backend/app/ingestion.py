"""知识入库管道：上传文件 → 提取文本 → 切分 → Embedding → 写入 Milvus。"""
import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app import db

ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}

# 递归切分：优先按段落切，段落太长再按句子、字符切，chunk 间留 80 字重叠保上下文
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80)


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def ingest_document(path: Path, filename: str) -> dict:
    from app.vectorstore import get_vectorstore  # 此处才连 Milvus

    text = extract_text(path)
    if not text.strip():
        raise ValueError("未能从文件中提取到文本（扫描版 PDF 需要先 OCR）")

    chunks = splitter.split_text(text)
    doc_id = uuid.uuid4().hex

    store = get_vectorstore()
    store.add_texts(
        chunks,
        metadatas=[
            {"doc_id": doc_id, "filename": filename, "chunk_index": i}
            for i in range(len(chunks))
        ],
    )
    db.insert_document(doc_id, filename, len(chunks))
    return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks)}


def delete_from_vectorstore(doc_id: str) -> None:
    try:
        from app.vectorstore import get_vectorstore

        store = get_vectorstore()
        store.col.delete(f'doc_id == "{doc_id}"')
    except Exception:
        pass  # Milvus 不可用时仅删除元数据，向量残留可接受
