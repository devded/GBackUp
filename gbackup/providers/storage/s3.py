import boto3
from typing import Any
from gbackup.core.interfaces import StorageProvider


class S3StorageProvider(StorageProvider):
    def __init__(
        self, endpoint_url: str, bucket_name: str, access_key: str, secret_key: str
    ):
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
        )

    def upload(self, file_path: str, object_key: str, callback: Any = None):
        self.client.upload_file(
            Filename=file_path,
            Bucket=self.bucket_name,
            Key=object_key,
            Callback=callback,
        )
