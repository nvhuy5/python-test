import logging
from utils import log_helpers
from models.class_models import DocumentType
from template_processors.processor_registry import POFileProcessorRegistry, MasterdataProcessorRegistry

# ===
# Set up logging
logger_name = f"Workflow Node - {__name__}"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===


def parse_file_to_json(self):  # pragma: no cover  # NOSONAR
    try:
        ext = self.file_record.get("file_extension")

        # Handle document type processor for Master Data and PO Data
        if self.document_type == DocumentType.ORDER:
            processor_class = POFileProcessorRegistry.get(ext)
        elif self.document_type == DocumentType.MASTER_DATA:
            processor_class = MasterdataProcessorRegistry.get(ext)
        else:
            logger.error(f"[parse_to_json] Unknown document type: {self.document_type}")
            return None

        if processor_class is None:
            logger.error(f"[parse_file_to_json] Unsupported file extension: {ext}")
            return None
        
        processor = processor_class.create_instance(file_path=self.file_path)
        json_data = processor.parse_file_to_json()
        return json_data

    except Exception as e:  # pragma: no cover  # NOSONAR
        logger.error(
            f"[parse_file_to_json] Failed to parse file: {e}", exc_info=True
        )
        return None
