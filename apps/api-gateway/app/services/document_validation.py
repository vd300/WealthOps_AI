from pathlib import Path

from fastapi import HTTPException, UploadFile, status


ALLOWED_UPLOAD_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
}


def validate_upload_metadata(file: UploadFile) -> str:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Supported file types are PDF, TXT, CSV, and XLSX.",
        )

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_UPLOAD_TYPES[extension]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Uploaded file content type does not match a supported document type.",
        )

    return extension


async def read_limited_upload(file: UploadFile, max_size_bytes: int) -> bytes:
    data = await file.read(max_size_bytes + 1)
    if len(data) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds the {max_size_bytes} byte size limit.",
        )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )
    return data
