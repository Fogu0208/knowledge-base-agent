"""文档管理接口：上传入库、列表、删除。"""
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app import db
from app.config import settings
from app.ingestion import ALLOWED_SUFFIXES, delete_from_vectorstore, ingest_document

router = APIRouter(tags=["documents"])


@router.post("/documents/upload")
async def upload_document(file: UploadFile):
    filename = file.filename or "untitled"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"暂不支持 {ext}，仅支持 pdf/txt/md")

    save_path = settings.UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    save_path.write_bytes(await file.read())

    try:
        result = ingest_document(save_path, filename)
    except ValueError as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(400, str(e))
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(502, f"入库失败（请确认 Milvus 已启动）：{e}")
    return result


@router.get("/documents")
def list_documents():
    return db.list_documents()


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    delete_from_vectorstore(doc_id)
    if not db.delete_document(doc_id):
        raise HTTPException(404, "文档不存在")
    return {"ok": True}
