import aioboto3
from src.config import config


class AWSStorageAsync:
    def __init__(self, bucket_name, region_name="eu-north-1"):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.session = aioboto3.Session()

    async def get_file_content(self, key: str) -> str | None:
        async with self.session.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        ) as s3_client:
            response = await s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = await response["Body"].read()
            return content.decode("utf-8")
