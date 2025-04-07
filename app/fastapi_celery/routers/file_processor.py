import io
import time
import traceback
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from utils import (
    log_helpers,
    read_n_write_s3
)
from models import request_info
from file_processors import (
    ext_detection,
    pdf_handling
)
from minio.error import S3Error

# ===
# Load environment variables from the .env file
from dotenv import load_dotenv
from configparser import ConfigParser
import json
from pathlib import Path

# ===
# Load environment variables from the .env file
load_dotenv(dotenv_path=f"{Path(__file__).parent.parent.parent.parent}/.env")
config = ConfigParser()
config.read(f"{Path(__file__).parent.parent}/configs.ini")
# Get the 'types' value
types_string = config.get('support_types', 'types')
types_list = json.loads(types_string)
# Get the 'bucket name' value
bucket_name = config.get('s3_buckets', 'converted_files')
# ===

# ===
# Set up logging
logger_name = 'Extension Detection Routers'
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

router = APIRouter()

# Submit a task
@router.post(
    "/process",
    summary="Extract file extension and feed into another function"
)
async def file_processor(request: request_info.FileRequest):
    
    # === Step 1 - Extract file extension === #
    try:
        file_processor  = ext_detection.FileExtensionProcessor(request.file_path)
        file_name       = file_processor.get_file_name_with_extension()
        file_extension  = file_processor.get_file_extension()
        file_record =  {
            'proceed_at': datetime.fromtimestamp(
                time.time_ns() / 1e9,
                timezone.utc
            ).strftime('%Y-%m-%d %H:%M:%S'),
            'file_path': request.file_path, 
            'file_name': file_name,
            'file_extension': file_extension,
        }

    # === Error handling ===
    # If a file is not found, return 404 error code
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {str(e)}"
        )
    # If there is a value error (e.g., invalid input), return 400 error code
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Value error: {str(e)}"
        )
    # Catch any other unexpected exceptions and log them
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )

    # === Step 2 - Feed into another function based on the file extension detected ===
    # If the file is not a PDF, return an error
    if file_record.get("file_extension") not in [f'.{type}' for type in types_list]:
        raise HTTPException(
            status_code=400,
            detail=f"Only {types_string} files are supported for content extraction."
        )
    if file_record.get('file_extension') == ".pdf":
        file_path           = file_record.get('file_path')
        file                = pdf_handling.PDFHandling(file=file_path)
        _, tables_found  = file.table_extraction()

        # show the DataFrame
        tab = tables_found[0]
        df = tab.to_pandas()
        print(df)

        # === Create a CSV file in Buffer and write directly to S3 bucket
        # Create an in-memory buffer using BytesIO for binary data
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        # Move the cursor to the beginning of the buffer after writing
        csv_buffer.seek(0)

        # Initialize MinIO client
        client = read_n_write_s3.S3FileProcessor(bucket_name=bucket_name)
        object_name = "chinese-table.csv"
        # Upload the CSV from the in-memory buffer to MinIO
        try:
            # Reset the buffer's position to the beginning before uploading
            csv_buffer.seek(0)
            client.put_object(object_name, csv_buffer)
            print(f"CSV file uploaded successfully to {bucket_name}/{object_name}.")
        except S3Error as e:
            print(f"Error uploading file to MinIO: {e}")

        return {
            'file_info': file_record,
            'status': 'Success'
        }
    