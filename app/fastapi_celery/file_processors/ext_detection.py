import os
from pathlib import Path
import logging
from utils import log_helpers

# ===
# Set up logging
logger_name = 'Extension Detection'  # You can give your logger any name you prefer
log_helpers.logging_config(logger_name)  # Apply the logging configuration
logger = logging.getLogger(logger_name)  # Get the logger instance
# ===

class FileExtensionProcessor:
    def __init__(self, file_path: Path):
        """Initializes the FileExtensionProcessor with the given file path."""
        if not isinstance(file_path, (str, Path)):
            raise ValueError("File path must be a string or a path to the file.")
        self.file_path = file_path
        self.extension = self.get_file_extension()
    
    def get_file_extension(self) -> str:
        """Detects and returns the file extension of the provided file."""
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"The file '{self.file_path}' does not exist.")
        
        # Using Pathlib to get the file extension
        file_extension = Path(self.file_path).suffix.lower()
        
        if not file_extension:
            raise ValueError(f"The file '{self.file_path}' has no extension.")
        
        logger.info(f"File extension detected: {file_extension}")
        return file_extension

    def get_file_name_with_extension(self) -> str:
        """Returns the full file name including the extension."""
        if not os.path.isfile(self.file_path):
            raise FileNotFoundError(f"The file '{self.file_path}' does not exist.")
        
        # Using Pathlib to get the full file name including extension
        file_name = Path(self.file_path).name
        
        logger.info(f"File name with extension detected: {file_name}")
        return file_name
