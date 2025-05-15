import config_loader
from models.class_models import DocumentType
from utils import log_helpers, read_n_write_s3
from pathlib import Path
import logging

# ===
# Set up logging
logger_name = f"Workflow Node - {__name__}"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

def write_raw_to_s3(self, source_file_path: str):
    # Check document type is Master data type
    if self.document_type == DocumentType.MASTER_DATA:  # pragma: no cover  # NOSONAR
        source_s3_raw_master_data = config_loader.get_config_value('s3_buckets', 'datahub_s3_raw_data')

        destination_s3_raw_master_name = config_loader.get_config_value("s3_buckets", "datahub_s3_master_data")
        file_name = Path(source_file_path).name
        stem = Path(source_file_path).stem
        destination_key = f"master_data/{stem}/{file_name}"
    
        try:
            logger.info("Preparing to write raw master data to s3")
            result = read_n_write_s3.copy_object_between_buckets(
                source_bucket = source_s3_raw_master_data,
                source_key = source_file_path,
                dest_bucket = destination_s3_raw_master_name,
                dest_key = destination_key
            )

            logger.info("write_raw_to_s3 completed.")
            return result

        except Exception as e:
            logger.error(f"Exception in write_raw_to_s3: {e}", exc_info=True)
            return None
