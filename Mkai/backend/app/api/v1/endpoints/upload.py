from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings

router = APIRouter()


@router.post("", response_model=dict)
async def upload_file(file: UploadFile = File(...)) -> dict:
    if file.content_type not in {"application/pdf", "text/plain", "application/json", "text/csv", "application/zip", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File exceeds size limit")

    return {"filename": file.filename, "size_bytes": len(content), "content_type": file.content_type}
