# import boto3
# import os
# from src.config import config
# from botocore.exceptions import NoCredentialsError, ClientError


# class AWSStorage:
#     def __init__(self, bucket_name, region_name="eu-north-1"):
#         self.bucket_name = bucket_name
#         self.region_name = region_name

#         self.s3 = boto3.client(
#             "s3",
#             region_name=region_name,
#             aws_access_key_id=config.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
#         )

#     def save_file(self, key, path):
#         try:
#             if not os.path.isfile(path):
#                 raise FileNotFoundError(f"Le fichier {path} n'existe pas.")

#             self.s3.upload_file(path, self.bucket_name, key)
#             print(f"Fichier uploadé avec succès : s3://{self.bucket_name}/{key}")
#             return True

#         except FileNotFoundError as e:
#             print("Erreur fichier :", e)
#             return False
#         except NoCredentialsError:
#             print("Credentials AWS introuvables.")
#             return False
#         except ClientError as e:
#             print("Erreur AWS :", e)
#             return False


# if __name__ == "__main__":
#     str0 = AWSStorage("prompt-parsing")
#     # str0.save_file("prompt1/file.md", "README.md")
