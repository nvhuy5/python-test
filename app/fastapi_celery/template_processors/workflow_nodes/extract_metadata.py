import time
import logging
from datetime import datetime, timezone
from utils import log_helpers, ext_extraction

# ===
# Set up logging
logger_name = f"Workflow Node - {__name__}"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

def extract_metadata(self):
    try:
        file_processor = ext_extraction.FileExtensionProcessor(self.file_path)
        self.document_type = file_processor.document_type
        self.file_record = {
            "file_path": self.file_path,
            "file_path_parent": file_processor.file_path_parent,
            "file_name": file_processor.file_name,
            "file_extension": file_processor.file_extension,
            "proceed_at": datetime.fromtimestamp(
                time.time_ns() / 1e9, timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }
        return True
    except FileNotFoundError as e:
        logger.error(f"[extract_metadata] File not found: {e}", exc_info=True)
    except ValueError as e:
        logger.error(f"[extract_metadata] Value error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"[extract_metadata] Unexpected error: {e}", exc_info=True)
    return False
