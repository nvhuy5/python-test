from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any
from utils.read_n_write_s3 import write_json_to_s3
from models.class_models import SourceType
from utils import log_helpers, ext_extraction
from models.class_models import PathEncoder
import config_loader

# ===
# Set up logging
logger_name = 'Excel Processor'
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

class MasterDataProcessor:
    def __init__(self, file_path: Path, source: SourceType = SourceType.S3):
        self.file_path = file_path
        self.file_object = None
        self.source = source

    # Text to json 
    def parse_file_to_json(self):
        file_object = ext_extraction.FileExtensionProcessor(file_path=self.file_path, source=self.source)
        self.file_object = file_object
        capacity = file_object._get_file_capacity()
        original_file_path = self.file_path

        if file_object.source == "local":
            with open(file_object.file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            # S3: read from in-memory buffer
            file_object.object_buffer.seek(0)
            text = file_object.object_buffer.read().decode("utf-8")

        blocks = text.strip().split("# Table: ")
        headers = {}
        items = {}

        for block in blocks:
            if not block.strip():
                continue

            lines = block.strip().splitlines()
            table_name = lines[0].strip()
            table_headers = lines[1].split("|")
            headers[table_name] = table_headers

            table_items = []
            for row in lines[2:]:
                values = row.split("|")
                item = dict(zip(table_headers, values))
                table_items.append(item)

            items[table_name] = table_items

        # Result dict
        result = {
            "original_file_path": original_file_path,
            "headers": headers,
            "items": items,
            "capacity": capacity
        }
        
        # Create the proceed master data
        self._upload_master_file_to_s3(result)
        return result

    def _upload_master_file_to_s3(self, json_data: Any):
        current_time = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        file_name = self.file_object.file_name.removesuffix(self.file_object.file_extension)
        object_name = f"process_data/{file_name}/{file_name}_{current_time}.json"
        bucket_name = config_loader.get_config_value("s3_buckets", "datahub_s3_master_data")
        file_record = {
            "file_name": file_name,
            "object_name": object_name
        }
        result = write_json_to_s3(json_data, file_record, bucket_name)
        return result
