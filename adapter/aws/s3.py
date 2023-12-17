import os
import errno
from botocore.exceptions import NoCredentialsError
from boto3 import session
from boto3_type_annotations.s3 import Client as S3Client


class S3Downloader:
    def __init__(self, _session: session.Session, bucket: str, download_dir: str):
        self.downloader: S3Client = _session.client("s3")
        self.bucket = bucket
        self.dir = download_dir

    def set_download_destination(self, destination: str):
        self.dir = destination

    def download_file(self, key: str):
        destination_file = os.path.join(self.dir, key)
        try:
            os.makedirs(os.path.dirname(destination_file))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        try:
            with open(destination_file, "wb") as fd:
                print(f"Downloading s3://{self.bucket}/{key} to {destination_file}...")
                self.downloader.download_fileobj(self.bucket, key, fd)
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
            response = self.downloader.get_object(Bucket=self.bucket, Key=key)
            return response
        except Exception as e:
            print(f"Error streaming file: {e}")
            return None

    def key_exists(self, key: str):
        try:
            self.downloader.head_object(Bucket=self.bucket, Key=key)
            return True
        except NoCredentialsError:
            print("Credentials not available")
            return False
        except self.downloader.exceptions.NoSuchKey:
            return False
        except Exception as e:
            print(f"Error checking if key exists: {e}")
            return False

    def list_objects_from_default_bucket(self, key: str):
        files = []
        try:
            paginator = self.downloader.get_paginator("list_objects_v2")
            response_iterator = paginator.paginate(Bucket=self.bucket, Prefix=key)

            for response in response_iterator:
                for obj in response.get("Contents", []):
                    files.append(obj["Key"])

        except Exception as e:
            print(f"Error listing objects: {e}")

        return files
