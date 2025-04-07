from minio import Minio
from minio.error import S3Error
import os
from dotenv import load_dotenv
from pathlib import Path
import io  # Ensure io module is imported

# === Load environment variables from .env file ===
load_dotenv(dotenv_path=f"{Path(__file__).parent.parent.parent.parent}/.env")

class S3FileProcessor:
    # Initialize Minio client
    def __init__(self, bucket_name: str):
        self.client = Minio(
            # Replace with your MinIO server address (e.g., minio:19000, localhost:9000)
            "172.26.174.66:19000",
            access_key=os.environ.get("S3_ACCESS_KEY"),
            secret_key=os.environ.get("S3_ACCESS_SECRET"),
            secure=False,  # Set to True if you're using HTTPS
        )
        self.bucket_name = bucket_name

        # Check if the bucket exists, and create it if not
        try:
            if not self.client.bucket_exists(self.bucket_name):
                print(f"Bucket '{self.bucket_name}' does not exist. Creating it now...")
                self.client.make_bucket(self.bucket_name)
            else:
                print(f"Bucket '{self.bucket_name}' already exists.")
        except S3Error as e:
            print("Error checking or creating bucket:", e)

    def put_object(self, object_name, uploading_data, **kwargs):
        try:
            # Check if uploading_data is a buffer-like object
            if isinstance(uploading_data, (io.BytesIO, io.StringIO)):
                uploading_data.seek(0)  # Reset buffer to the beginning
                file_size = len(uploading_data.getvalue())
                # Perform the upload from buffer
                self.client.put_object(
                    self.bucket_name,
                    object_name,
                    uploading_data,
                    file_size
                )
                print(f"Buffer data uploaded successfully to {self.bucket_name}/{object_name}.")
            
            # If it's not a buffer, assume it's a file path
            elif isinstance(uploading_data, str):
                # Upload the file to MinIO
                file_path = uploading_data
                try:
                    self.client.fput_object(self.bucket_name, object_name, file_path)
                    print(f"File '{file_path}' uploaded successfully to '{self.bucket_name}/{object_name}'.")
                except S3Error as e:
                    print(f"Error occurred: {e}")
            
            else:
                raise TypeError("uploading_data must be either a buffer-like object or a file path")

        except (S3Error, TypeError) as e:
            print(f"Error uploading file to MinIO: {e}")
