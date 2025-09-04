import os

import aioboto3.session
import aioboto3
from botocore.exceptions import NoCredentialsError, ClientError
from src.config import config


class AWSStorageAsync:
    def __init__(self, bucket_name, region_name="eu-north-1"):
        self.bucket_name = bucket_name
        self.region_name = region_name

    async def save_file(self, key, path):
        if not os.path.isfile(path):
            print(f"Le fichier {path} n'existe pas.")
            return False

        session = aioboto3.Session()

        try:
            async with session.client(
                "s3",
                region_name=self.region_name,
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
            ) as s3_client:
                await s3_client.upload_file(path, self.bucket_name, key)
                print(f"Fichier uploadé avec succès : s3://{self.bucket_name}/{key}")
                return True

        except FileNotFoundError as e:
            print("Erreur fichier :", e)
            return False
        except NoCredentialsError:
            print("Credentials AWS introuvables.")
            return False
        except ClientError as e:
            print("Erreur AWS :", e)
            return False


# Exécution de manière asynchrone
if __name__ == "__main__":
    import asyncio

    async def main():
        storage = AWSStorageAsync("test-outputs")
        await storage.save_file("test_file/file.md", "README.md")

    asyncio.run(main())