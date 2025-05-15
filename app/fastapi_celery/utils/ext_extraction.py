import os
import json
import traceback
from pathlib import Path, PurePosixPath
import logging

from utils import log_helpers, read_n_write_s3
from connections import aws_connection
from models.class_models import SourceType, DocumentType

import config_loader

# === Logging Setup ===
logger_name = 'Extension Detection'
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)

types_string = config_loader.get_config_value('support_types', 'types')
types_list = json.loads(types_string)
datahub_s3_raw_data = config_loader.get_config_value('s3_buckets', 'datahub_s3_raw_data')

class FileExtensionProcessor:
    def __init__(self, file_path: str, source: SourceType = SourceType.S3):  # pragma: no cover  # NOSONAR
        if not isinstance(file_path, (str, Path)):
            raise ValueError("file_path must be a string or Path.")
        
        self.file_path = str(file_path)
        self.file_path_parent = None
        self.source = source
        self.object_buffer = None
        self.file_extension = None
        self.file_name = None
        self.client = None
        self.document_type = self._get_document_type()

        self._prepare_object()

    def _prepare_object(self):
        logger.info(f"Loading file from {self.source}...")
        if self.source == SourceType.LOCAL:
            self._load_local_file()
        else:
            self._load_s3_file()
        
        self._extract_file_extension()

    def _load_local_file(self):
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"Local file '{self.file_path}' does not exist.")
        self.file_name = Path(self.file_path).name
        self.file_path_parent = str(Path(self.file_path).parent) + "/"

    def _load_s3_file(self): # pragma: no cover  # NOSONAR
        try:
            s3_connector = aws_connection.S3Connector(bucket_name=datahub_s3_raw_data)
            self.client = s3_connector.client
            self._get_file_capacity()

            buffer = read_n_write_s3.get_object(
                client=self.client,
                bucket_name=datahub_s3_raw_data,
                object_name=self.file_path
            )

            if not buffer:  # pragma: no cover  # NOSONAR
                logger.error(f"S3 object '{self.file_path}' not found - {traceback.format_exc()}")
                raise FileNotFoundError(f"S3 object '{self.file_path}' not found.")

            self.object_buffer = buffer
            self.file_name = Path(self.file_path).name
            self.file_path_parent = str(Path(self.file_path).parent) + "/"

        except Exception:
            logger.error(f"Error accessing file '{self.file_path}': {traceback.format_exc()}")
            raise FileNotFoundError(f"File '{self.file_path}' could not be loaded from S3.")

    def _extract_file_extension(self): # pragma: no cover  # NOSONAR
        suffix = Path(self.file_path).suffix.lower()
        if not suffix:
            logger.error("The file does not have an extension.")
            raise ValueError(f"File '{self.file_path}' has no extension.")

        if suffix not in types_list:
            logger.error(f"Unsupported file type: {suffix}")
            raise TypeError(
                f"Unsupported file extension '{suffix}'. Allowed types: {types_string}"
            )

        self.file_extension = suffix
        logger.info(f"File extension detected: {self.file_extension}")

    # Function to calculate the size of a file
    def _get_file_capacity(self) -> str: # pragma: no cover  # NOSONAR
        if self.source == SourceType.LOCAL:
            size_bytes = os.path.getsize(self.file_path)
        else:
            # Use head_object for file size info (standard in boto3)
            head = self.client.head_object(Bucket=datahub_s3_raw_data, Key=self.file_path)
            size_bytes = head.get("ContentLength", 0)
        
        if size_bytes / (1024**2) >= 1:
            size_mb = size_bytes / (1024**2)
            logger.info(f"Size of the input file {self.file_path} in MB: {size_mb:.2f}")
            return f"{size_mb:.2f} MB"
        else:
            size_kb = size_bytes / 1024
            logger.info(f"Size of the input file {self.file_path} in KB: {size_kb:.2f}")
            return f"{size_kb:.2f} KB"
    
    # Extracts the root directory from a file path to determine the document type.
    def _get_document_type(self) -> DocumentType:
        """
        Extracts the root directory from a file path to determine the document type.
        :return: DocumentType indicating the document type based on the root directory.
        :raises ValueError: If the file path is invalid or cannot be parsed correctly.
        """
        try:
            if self.source == SourceType.LOCAL:
                parts = Path(os.path.normpath(self.file_path)).parts
            else:
                parts = PurePosixPath(self.file_path).parts

            if not parts:
                logger.error(f"Invalid file path: '{self.file_path}'. No path components found.")
                raise ValueError(f"Invalid file path: '{self.file_path}'. No path components found.")
            
            logger.info(f"The file_path's exposed: {parts}")
            if any(part.lower() == "master_data" for part in parts):
                return DocumentType.MASTER_DATA
            else:
                return DocumentType.ORDER

        except Exception as e:
            logger.error(f"Error determining document type from path '{self.file_path}': {traceback.format_exc()}")
            raise ValueError(f"Error determining document type from path '{self.file_path}': {e}")
