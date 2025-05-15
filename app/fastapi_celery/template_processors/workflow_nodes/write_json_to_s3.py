import config_loader
from models.class_models import DocumentType, PathEncoder
from utils import log_helpers, read_n_write_s3
import logging
import json

# ===
# Set up logging
logger_name = f"Workflow Node - {__name__}"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

def write_json_to_s3(self, input_data, s3_key_prefix: str = ""):
    # Define the target bucket based on the document type of PO and Master Data
    if self.document_type == DocumentType.ORDER:
        bucket_name = config_loader.get_config_value("s3_buckets", "datahub_s3_process_data")
    elif self.document_type == DocumentType.MASTER_DATA:  # pragma: no cover  # NOSONAR
        bucket_name = config_loader.get_config_value("s3_buckets", "datahub_s3_master_data")
    else: # pragma: no cover  # NOSONAR
        logger.error(f"[write_json_to_s3] Unknown document type: {self.document_type}")
        return None
    
    if not input_data:  # pragma: no cover  # NOSONAR
        logger.warning("No input data provided to write_json_to_s3.")
        return None
    
    logger.debug(f"input_data: {input_data} - type: {type(input_data)}")
    try:
        logger.info("Preparing to write JSON to S3")
        result = read_n_write_s3.write_json_to_s3(
            json_data=input_data,
            file_record=self.file_record,
            bucket_name=bucket_name,
            s3_key_prefix=s3_key_prefix
        )

        logger.info("write_json_to_s3 completed.")
        return result

    except Exception as e:
        logger.error(f"Exception in write_json_to_s3: {e}", exc_info=True)
        return None
