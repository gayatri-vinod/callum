"""Object storage for callum uploads.

Backends:
- minio — S3-compatible object store (production path)
- local — filesystem under UPLOAD_DIR (dev fallback)

`storage_backend=auto` tries MinIO and falls back to local if unreachable.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import aiofiles
from minio import Minio
from minio.error import S3Error

from app.core.config import settings


@dataclass
class StoredObject:
    uri: str
    backend: str  # minio | local
    bucket: str | None
    key: str
    size_bytes: int


class StorageError(RuntimeError):
    pass


def object_key(project_id: str, document_id: str, filename: str) -> str:
    safe_name = Path(filename).name.replace("\\", "_").replace("/", "_")
    return f"projects/{project_id}/{document_id}/{safe_name}"


def parse_uri(uri: str) -> tuple[str, str | None, str]:
    """Return (backend, bucket|None, key_or_path)."""
    if uri.startswith("minio://"):
        rest = uri[len("minio://") :]
        bucket, _, key = rest.partition("/")
        return "minio", bucket, key
    if uri.startswith("file://"):
        return "local", None, uri[len("file://") :]
    # legacy absolute/relative filesystem paths from step 1
    return "local", None, uri


class LocalStorage:
    backend = "local"

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    async def ensure_ready(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    async def put_bytes(
        self,
        *,
        project_id: str,
        document_id: str,
        filename: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        key = object_key(project_id, document_id, filename)
        dest = self.root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(dest, "wb") as f:
            await f.write(data)
        uri = f"file://{dest.resolve().as_posix()}"
        return StoredObject(
            uri=uri,
            backend=self.backend,
            bucket=None,
            key=key,
            size_bytes=len(data),
        )

    async def get_bytes(self, uri: str) -> tuple[bytes, str | None]:
        _, _, path = parse_uri(uri)
        file_path = Path(path)
        if not file_path.exists():
            raise StorageError(f"object not found: {uri}")
        async with aiofiles.open(file_path, "rb") as f:
            data = await f.read()
        return data, None

    async def delete(self, uri: str) -> None:
        _, _, path = parse_uri(uri)
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()

    async def exists(self, uri: str) -> bool:
        _, _, path = parse_uri(uri)
        return Path(path).exists()


class MinioStorage:
    backend = "minio"

    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def _ensure_bucket_sync(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    async def ensure_ready(self) -> None:
        await asyncio.to_thread(self._ensure_bucket_sync)

    def _put_sync(
        self, key: str, data: bytes, content_type: str | None
    ) -> None:
        self.client.put_object(
            self.bucket,
            key,
            BytesIO(data),
            length=len(data),
            content_type=content_type or "application/octet-stream",
        )

    def _get_sync(self, key: str) -> tuple[bytes, str | None]:
        response = self.client.get_object(self.bucket, key)
        try:
            data = response.read()
            content_type = response.headers.get("Content-Type")
            return data, content_type
        finally:
            response.close()
            response.release_conn()

    def _delete_sync(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def _stat_sync(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except S3Error:
            return False

    async def put_bytes(
        self,
        *,
        project_id: str,
        document_id: str,
        filename: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        key = object_key(project_id, document_id, filename)
        await asyncio.to_thread(self._put_sync, key, data, content_type)
        uri = f"minio://{self.bucket}/{key}"
        return StoredObject(
            uri=uri,
            backend=self.backend,
            bucket=self.bucket,
            key=key,
            size_bytes=len(data),
        )

    async def get_bytes(self, uri: str) -> tuple[bytes, str | None]:
        backend, bucket, key = parse_uri(uri)
        if backend != "minio":
            raise StorageError(f"not a minio uri: {uri}")
        if bucket and bucket != self.bucket:
            raise StorageError(f"unexpected bucket: {bucket}")
        try:
            return await asyncio.to_thread(self._get_sync, key)
        except S3Error as exc:
            raise StorageError(f"object not found: {uri}") from exc

    async def delete(self, uri: str) -> None:
        _, _, key = parse_uri(uri)
        await asyncio.to_thread(self._delete_sync, key)

    async def exists(self, uri: str) -> bool:
        _, _, key = parse_uri(uri)
        return await asyncio.to_thread(self._stat_sync, key)

    def presigned_get_url(self, uri: str, expires_seconds: int = 3600) -> str:
        from datetime import timedelta

        _, _, key = parse_uri(uri)
        return self.client.presigned_get_object(
            self.bucket,
            key,
            expires=timedelta(seconds=expires_seconds),
        )


class StorageService:
    def __init__(self, backend: LocalStorage | MinioStorage) -> None:
        self._backend = backend

    @property
    def backend_name(self) -> str:
        return self._backend.backend

    async def ensure_ready(self) -> None:
        await self._backend.ensure_ready()

    async def put_bytes(
        self,
        *,
        project_id: str,
        document_id: str,
        filename: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        return await self._backend.put_bytes(
            project_id=project_id,
            document_id=document_id,
            filename=filename,
            data=data,
            content_type=content_type,
        )

    async def get_bytes(self, uri: str) -> tuple[bytes, str | None]:
        backend, _, _ = parse_uri(uri)
        if backend == "minio" and isinstance(self._backend, MinioStorage):
            return await self._backend.get_bytes(uri)
        if backend == "local":
            local = (
                self._backend
                if isinstance(self._backend, LocalStorage)
                else LocalStorage(settings.upload_dir)
            )
            return await local.get_bytes(uri)
        # Cross-read: uri says minio but runtime is local (or vice versa)
        if backend == "minio":
            return await MinioStorage().get_bytes(uri)
        return await LocalStorage(settings.upload_dir).get_bytes(uri)

    async def delete(self, uri: str) -> None:
        backend, _, _ = parse_uri(uri)
        if backend == "minio":
            await MinioStorage().delete(uri)
        else:
            await LocalStorage(settings.upload_dir).delete(uri)

    async def exists(self, uri: str) -> bool:
        backend, _, _ = parse_uri(uri)
        if backend == "minio":
            return await MinioStorage().exists(uri)
        return await LocalStorage(settings.upload_dir).exists(uri)


def _minio_reachable() -> bool:
    try:
        client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        client.list_buckets()
        return True
    except Exception:
        return False


@lru_cache
def get_storage() -> StorageService:
    mode = (settings.storage_backend or "auto").lower()
    if mode == "local":
        return StorageService(LocalStorage(settings.upload_dir))
    if mode == "minio":
        return StorageService(MinioStorage())
    # auto
    if _minio_reachable():
        return StorageService(MinioStorage())
    return StorageService(LocalStorage(settings.upload_dir))


def content_disposition(filename: str) -> str:
    return f"attachment; filename*=UTF-8''{quote(filename)}"
