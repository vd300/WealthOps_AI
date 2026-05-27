from io import BytesIO
from urllib.parse import urlparse

from app.core.config import Settings


class ObjectStorageClient:
    def __init__(self, settings: Settings) -> None:
        from minio import Minio

        parsed_url = urlparse(settings.object_storage_url)
        endpoint = parsed_url.netloc or parsed_url.path
        secure = parsed_url.scheme == "https"
        self._bucket = settings.object_storage_bucket
        self._client = Minio(
            endpoint,
            access_key=settings.object_storage_access_key,
            secret_key=settings.object_storage_secret_key.get_secret_value(),
            secure=secure,
        )

    @property
    def bucket(self) -> str:
        return self._bucket

    def put_object(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

        self._client.put_object(
            self._bucket,
            object_key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
