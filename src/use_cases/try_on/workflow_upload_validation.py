"""Upload-validation helpers for the Try-On workflow service."""
from __future__ import annotations

from hashlib import sha256

from fastapi import UploadFile

from src.domain.try_on import TryOnError, TryOnErrorCode, TryOnInputMetadata, TryOnUploadRole

from .workflow_models import TryOnUploadValidationConfig, TryOnValidationError, ValidatedTryOnUpload


def missing_fields(
    human_photo: UploadFile | None,
    garment_photo: UploadFile | None,
    upper_garment_photo: UploadFile | None = None,
    lower_garment_photo: UploadFile | None = None,
    outerwear_garment_photo: UploadFile | None = None,
    full_body_garment_photo: UploadFile | None = None,
) -> list[str]:
    """Return request fields that did not include an upload."""
    fields: list[str] = []
    if human_photo is None:
        fields.append(TryOnUploadRole.HUMAN_PHOTO.value)
    garment_uploads = [
        garment_photo,
        upper_garment_photo,
        lower_garment_photo,
        outerwear_garment_photo,
        full_body_garment_photo,
    ]
    if all(upload is None for upload in garment_uploads):
        fields.append(TryOnUploadRole.GARMENT_PHOTO.value)
    return fields


async def validate_upload(
    *,
    role: TryOnUploadRole,
    upload: UploadFile | None,
    validation: TryOnUploadValidationConfig,
) -> ValidatedTryOnUpload:
    """Read and validate upload bytes before returning metadata and payload."""
    if upload is None:
        raise validation_error(
            TryOnErrorCode.MISSING_REQUIRED_FILE,
            "Required upload is missing.",
            {"fields": [role.value]},
        )

    content_type = upload.content_type or ""
    if content_type not in validation.allowed_content_types:
        raise validation_error(
            TryOnErrorCode.UNSUPPORTED_CONTENT_TYPE,
            "Upload content type is not supported.",
            {
                "field": role.value,
                "content_type": content_type,
                "allowed_content_types": sorted(validation.allowed_content_types),
            },
        )

    await upload.seek(0)
    payload = await upload.read()
    await upload.seek(0)
    size_bytes = len(payload)
    if size_bytes == 0:
        raise validation_error(
            TryOnErrorCode.EMPTY_FILE,
            "Uploaded file is empty.",
            {"field": role.value},
        )
    if size_bytes > validation.max_upload_bytes:
        raise validation_error(
            TryOnErrorCode.FILE_TOO_LARGE,
            "Uploaded file exceeds the configured size limit.",
            {
                "field": role.value,
                "size_bytes": size_bytes,
                "max_upload_bytes": validation.max_upload_bytes,
            },
        )

    metadata = TryOnInputMetadata(
        role=role,
        filename=upload.filename or role.value,
        content_type=content_type,
        size_bytes=size_bytes,
        sha256=sha256(payload).hexdigest(),
    )
    return ValidatedTryOnUpload(metadata=metadata, payload=payload)


def validation_error(
    code: TryOnErrorCode,
    message: str,
    details: dict[str, object],
) -> TryOnValidationError:
    """Build a typed validation exception."""
    return TryOnValidationError(TryOnError(code=code, message=message, details=details))
