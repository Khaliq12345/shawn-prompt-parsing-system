import sys

sys.path.append(".")

import boto3
from src.config import config


class AWSStorage:
    def __init__(self, bucket_name, region_name="eu-north-1"):
        self.bucket_name = bucket_name
        self.region_name = region_name
        self.s3_client = boto3.client(
            "s3",
            region_name=self.region_name,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
        )

    def get_file_content(self, key: str) -> str | None:
        print("Download from s3 bucket")
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        content = response["Body"].read()
        return content.decode("utf-8")

    def get_presigned_url(self, key: str) -> str | None:
        print("Generating URL")
        response = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
        )
        return response


if __name__ == "__main__":
    aws = AWSStorage("browser-outputs")
    aws.get_presigned_url("chatgpt/1756805263/screenshot.png")
