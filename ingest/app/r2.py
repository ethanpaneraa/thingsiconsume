import os
import boto3
from botocore.config import Config
from typing import Optional


_s3_client: Optional[boto3.client] = None


def get_s3_client():
    """Get or create S3 client for R2."""
    global _s3_client
    if _s3_client is None:
        endpoint_url = os.getenv("R2_ENDPOINT_URL")
        access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")

        if not all([endpoint_url, access_key_id, secret_access_key]):
            raise ValueError("R2 credentials not configured")

        _s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4")
        )

    return _s3_client


def upload_to_r2(key: str, data: bytes, content_type: str) -> None:
    """
    Upload data to R2 bucket.

    Args:
        key: R2 object key (path)
        data: Bytes to upload
        content_type: Content-Type header value
    """
    bucket_name = os.getenv("R2_BUCKET_NAME")
    if not bucket_name:
        raise ValueError("R2_BUCKET_NAME environment variable not set")

    s3_client = get_s3_client()

    s3_client.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=data,
        ContentType=content_type
    )

