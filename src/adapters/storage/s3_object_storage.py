"""S3-compatible object storage adapter."""

from __future__ import annotations

import importlib
from datetime import timedelta

from src.domain.try_on import utc_now

from .contracts import SignedUrl, StoredObject


class S3ObjectStorage:
    """Thin S3 client wrapper for future artifact persistence workflows."""

    def __init__(
        self,
        *,
        bucket_name: str,
        endpoint_url: str | None,
        region_name: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
    ) -> None:
        """Initialize the S3 client with portable configuration."""
        self._bucket_name = bucket_name
        self._client = self._build_client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region_name,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def put_bytes(self, *, object_key: str, payload: bytes, content_type: str) -> StoredObject:
        """Store bytes in S3-compatible storage and return portable metadata."""
        response = self._client.put_object(
            Bucket=self._bucket_name,
            Key=object_key,
            Body=payload,
            ContentType=content_type,
        )
        etag = response.get("ETag")
        if isinstance(etag, str):
            etag = etag.strip('"')
        return StoredObject(
            bucket_name=self._bucket_name,
            object_key=object_key,
            content_type=content_type,
            content_length=len(payload),
            etag=etag if isinstance(etag, str) else None,
            version_id=response.get("VersionId") if isinstance(response.get("VersionId"), str) else None,
            storage_backend="s3",
        )

    def get_bytes(self, object_key: str) -> bytes:
        """Read raw bytes from S3-compatible storage for provider-side processing."""
        response = self._client.get_object(Bucket=self._bucket_name, Key=object_key)
        body = response["Body"]
        return body.read()

    def create_signed_get_url(self, object_key: str, *, expires_in_seconds: int) -> SignedUrl:
        """Return a presigned GET URL for a stored object."""
        url = self._client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self._bucket_name, "Key": object_key},
            ExpiresIn=expires_in_seconds,
        )
        return SignedUrl(
            url=url,
            expires_at=utc_now() + timedelta(seconds=expires_in_seconds),
            method="GET",
        )

    @staticmethod
    def _build_client(*args, **kwargs):
        """Create the boto3 S3 client lazily so non-S3 runtimes do not require boto3 at import time."""
        try:
            boto3 = importlib.import_module("boto3")
        except ModuleNotFoundError as exc:
            raise RuntimeError("boto3 is required when object_storage_backend is s3") from exc
        return boto3.client(*args, **kwargs)
