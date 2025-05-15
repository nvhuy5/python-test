import logging
from utils import log_helpers
from models.class_models import DocumentType

# ===
# Set up logging
logger_name = f"Workflow Node - {__name__}"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===


def publish_data(self):
    # This method is intentionally left blank.
    # Subclasses or future implementations should override this to provide validation logic.
    pass