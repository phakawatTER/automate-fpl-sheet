import os
import errno
from typing import Optional
from botocore.exceptions import NoCredentialsError, BotoCoreError, ClientError
from boto3.session import Session
from boto3_type_annotations.s3 import Client as S3Client
import util


class S3Downloader:
    def __init__(self, session: Session, bucket: str, download_dir: str):
        self.__downloader: S3Client = session.client("s3")
        self.__bucket = bucket
        self.__dir = download_dir

    def set_download_destination(self, destination: str):
        self.__dir = destination

    @util.time_track(description="Dowload File")
    def download_file(self, key: str):
        destination_file = os.path.join(self.__dir, key)
        try:
            os.makedirs(os.path.dirname(destination_file))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        try:
            with open(destination_file, "wb") as fd:
                print(
                    f"Downloading s3://{self.__bucket}/{key} to {destination_file}..."
                )
                self.__downloader.download_fileobj(self.__bucket, key, fd)
            return destination_file
        except NoCredentialsError:
            print("Credentials not available")
            return None
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None

    def download_file_from_default_bucket(self, key: str):
        return self.download_file(key)

    def stream_file_from_default_bucket(self, key: str):
        try:
            response = self.__downloader.get_object(Bucket=self.__bucket, Key=key)
            return response
        except Exception as e:
            print(f"Error streaming file: {e}")
            return None

    def key_exists(self, key: str):
        try:
            self.__downloader.head_object(Bucket=self.__bucket, Key=key)
            return True
        except NoCredentialsError:
            print("Credentials not available")
            return False
        except self.__downloader.exceptions.NoSuchKey:
            return False
        except Exception as e:
            print(f"Error checking if key exists: {e}")
            return False

    def list_objects_from_default_bucket(self, key: str):
        files = []
        try:
            paginator = self.__downloader.get_paginator("list_objects_v2")
            response_iterator = paginator.paginate(Bucket=self.__bucket, Prefix=key)

            for response in response_iterator:
                for obj in response.get("Contents", []):
                    files.append(obj["Key"])

        except Exception as e:
            print(f"Error listing objects: {e}")

        return files


class S3Uploader:
    def __init__(self, session: Session, bucket: str):
        self.__s3_client: S3Client = session.client("s3")
        self.__bucket = bucket

    @util.time_track(description="Upload File")
    def upload(self, key, content_type, filename, expires=None):
        params = {
            "Bucket": self.__bucket,
            "Key": key,
            "Filename": filename,
        }

        try:
            response = self.__s3_client.upload_file(**params)
            return response
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Error uploading to S3: {str(e)}") from e

    def upload_to_default_bucket(
        self,
        key: str,
        content_type: str,
        filename,
        expires: Optional[int] = None,
    ):
        return self.upload(key, content_type, filename, expires)

    def generate_presigned_url(self, key, expiration_time=3600):
        """
        Generate a pre-signed URL for the specified S3 object.

        Parameters:
        - key: The key of the S3 object.
        - expiration_time: The expiration time of the URL in seconds (default is 1 hour).

        Returns:
        - str: The pre-signed URL.
        """
        params = {
            "Bucket": self.__bucket,
            "Key": key,
        }

        url = self.__s3_client.generate_presigned_url(
            "get_object", Params=params, ExpiresIn=expiration_time
        )

        return url
