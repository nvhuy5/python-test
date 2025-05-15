import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import logging
import traceback
from fastapi_celery.utils import log_helpers
from fastapi_celery.connections import aws_connection
from fastapi_celery.models.class_models import SourceType, DocumentType
from fastapi_celery.utils.ext_extraction import FileExtensionProcessor
from fastapi_celery.utils.log_helpers import logging_config

logger_name = 'Extension Detection'
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)

# Constants used in tests
OS_PATH_ISFILE = "os.path.isfile"
TYPES_STRING = '[".pdf", ".txt", ".csv"]'
BUCKET_NAME = 'test-bucket'

# Define the mock configurations
@pytest.fixture
def mock_config():
    with patch("fastapi_celery.utils.ext_extraction.config_loader.get_config_value") as mock_config_value:
        mock_config_value.side_effect = lambda section, key: TYPES_STRING if key == "types" else BUCKET_NAME
        yield mock_config_value

# Mock for logging to avoid actual logs being written during tests
@pytest.fixture
def mock_logger():
    with patch("fastapi_celery.utils.ext_extraction.logger") as mock_logger:
        yield mock_logger

# === Test Cases ===
def test_file_extension_processor_local_file(mock_config, mock_logger):
    file_path = "path/to/local_file.txt"

    # Mock for os.path.isfile to simulate file existence
    with patch(OS_PATH_ISFILE, return_value=True):
        processor = FileExtensionProcessor(file_path=file_path, source=SourceType.LOCAL)

        assert processor.file_name == "local_file.txt"
        assert os.path.normpath(str(processor.file_path_parent)) == os.path.normpath("path/to/")
        assert processor.file_extension == ".txt"


def test_file_extension_processor_local_file_not_found(mock_config, mock_logger):
    file_path = "path/to/non_existent_file.txt"

    # Mock for os.path.isfile to simulate file non-existence (False)
    with patch(OS_PATH_ISFILE, return_value=False):
        with pytest.raises(FileNotFoundError, match=f"Local file '{file_path}' does not exist."):
            FileExtensionProcessor(file_path=file_path, source=SourceType.LOCAL)


def test_file_extension_processor_invalid_extension(mock_config, mock_logger):
    file_path = "path/to/unsupported_file.xyz"

    # Mock for os.path.isfile to simulate file non-existence (False)
    with patch(OS_PATH_ISFILE, return_value=False):
        with pytest.raises(FileNotFoundError):
            FileExtensionProcessor(file_path=file_path, source=SourceType.LOCAL)


# === Test for _get_document_type ===
# Patch the necessary methods and classes to mock the S3 behavior
@patch("fastapi_celery.utils.ext_extraction.read_n_write_s3.get_object", return_value=b"dummy content")
@patch("fastapi_celery.utils.ext_extraction.aws_connection.S3Connector")
def test_get_document_type_s3(mock_s3_connector, mock_get_object, mock_config, mock_logger):
    mock_client = MagicMock()
    mock_s3_connector.return_value.client = mock_client
    mock_client.head_object.return_value = {"ContentLength": 1024 * 1024 * 5}  # 5 MB

    file_path = "bucket_name/folder/data.csv"
    processor = FileExtensionProcessor(file_path=file_path, source=SourceType.S3)

    document_type = processor._get_document_type()
    assert document_type == DocumentType.ORDER


@patch("fastapi_celery.utils.ext_extraction.read_n_write_s3.get_object", return_value=b"dummy content")
@patch("fastapi_celery.utils.ext_extraction.aws_connection.S3Connector")
def test_get_document_type_master_data(mock_s3_connector, mock_get_object, mock_config, mock_logger):
    mock_client = MagicMock()
    mock_s3_connector.return_value.client = mock_client
    mock_client.head_object.return_value = {"ContentLength": 1024 * 1024 * 5}  # 5 MB

    file_path = "DKSH_SFTP/MASTER_DATA/file.csv"
    processor = FileExtensionProcessor(file_path=file_path, source=SourceType.S3)

    document_type = processor._get_document_type()
    assert document_type == DocumentType.MASTER_DATA

@patch("fastapi_celery.utils.ext_extraction.read_n_write_s3.get_object", return_value=b"dummy content")
@patch("fastapi_celery.utils.ext_extraction.aws_connection.S3Connector")
@patch(OS_PATH_ISFILE, return_value=True)
def test_get_document_type_order_local(mock_s3_connector, mock_get_object, mock_config, mock_logger):
    file_path = "NOT_MASTER_DATA\\SAP_Master_data.txt"
    processor = FileExtensionProcessor(file_path=file_path, source=SourceType.LOCAL)

    document_type = processor._get_document_type()
    assert document_type == DocumentType.ORDER


# === Test for _load_s3_file ===
@patch("fastapi_celery.utils.ext_extraction.read_n_write_s3.get_object")
@patch("fastapi_celery.utils.ext_extraction.aws_connection.S3Connector")
def test_load_s3_file_success(mock_s3_connector_cls, mock_get_object):
    file_path = "path/to/file.txt"

    # Setup mock connector and client
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ContentLength": 1024 * 1024 * 10}
    mock_s3_connector = MagicMock()
    mock_s3_connector.client = mock_client
    mock_s3_connector_cls.return_value = mock_s3_connector

    # Mock buffer return
    mock_buffer = MagicMock()
    mock_get_object.return_value = mock_buffer

    processor = FileExtensionProcessor(file_path=file_path, source=SourceType.S3)

    assert processor.object_buffer == mock_buffer
    assert processor.file_name == Path(file_path).name
    assert processor.file_path_parent == str(Path(file_path).parent) + "/"


@patch("fastapi_celery.utils.ext_extraction.read_n_write_s3.get_object")
@patch("fastapi_celery.utils.ext_extraction.aws_connection.S3Connector")
def test_load_s3_file_not_found(mock_s3_connector_cls, mock_get_object):
    file_path = "path/to/nonexistent_file.txt"

    # Set up the mock client to simulate failure in head_object
    mock_client = MagicMock()
    mock_client.head_object.side_effect = Exception("Simulated head_object failure")

    # Set up the S3Connector to return the mocked client
    mock_s3_connector = MagicMock()
    mock_s3_connector.client = mock_client
    mock_s3_connector_cls.return_value = mock_s3_connector

    # Run the test
    with pytest.raises(FileNotFoundError, match=f"File '{file_path}' could not be loaded from S3"):
        FileExtensionProcessor(file_path=file_path, source=SourceType.S3)

# === Log helper ===
@pytest.mark.parametrize('mock_has_handlers', [False])
@patch('logging.getLogger')
def test_logging_config(mock_get_logger, mock_has_handlers):
    mock_log = mock_get_logger.return_value
    mock_log.hasHandlers.return_value = mock_has_handlers

    # Call the function under test
    logging_config("test_logger")

    # Assertions to ensure your logging configuration logic is being tested
    assert mock_log.handlers
    mock_log.handlers.clear.assert_not_called()
