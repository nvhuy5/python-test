import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi_celery.models.class_models import PathEncoder, SourceType
from fastapi_celery.template_processors.master_data_processors import txt_master_data_processor


@pytest.fixture
def base_path():
    return Path(__file__).parent / "samples"


def test_masterdata_itemvalue(base_path):
    file_path = base_path / "SAP_Master_data.txt"
    masterdata = txt_master_data_processor.MasterDataProcessor(file_path, SourceType.LOCAL).parse_file_to_json()

    print(masterdata)
    file_path = Path(masterdata["original_file_path"])
    assert file_path.name == "SAP_Master_data.txt"
    assert isinstance(masterdata['capacity'], str)
    assert "KB" in masterdata['capacity']


def test_path_encoder_serializes_path_platform_aware():
    if sys.platform.startswith("win"):
        path = Path("C:\\Users\\test\\file.txt")
        expected = '{"path": "C:/Users/test/file.txt"}'
    else:
        path = Path("/home/test/file.txt")
        expected = '{"path": "/home/test/file.txt"}'

    data = {"path": path}
    result = json.dumps(data, cls=PathEncoder)
    assert result == expected


@patch("fastapi_celery.template_processors.master_data_processors.txt_master_data_processor.ext_extraction.FileExtensionProcessor")
def test_parse_file_to_json_from_s3(mock_processor_class):
    mock_processor = MagicMock()
    mock_processor.source = "s3"
    mock_processor._get_file_capacity.return_value = "2.5 KB"
    mock_processor.file_name = "sample.txt"
    mock_processor.file_extension = ".txt"
    mock_processor.object_buffer.read.return_value = b"# Table: Products\nid|name\n1|Apple\n2|Banana"
    mock_processor.object_buffer.seek.return_value = None
    mock_processor_class.return_value = mock_processor

    processor = txt_master_data_processor.MasterDataProcessor(file_path=Path("s3://dummy-path/sample.txt"), source=SourceType.S3)
    result = processor.parse_file_to_json()

    assert result["headers"] == {"Products": ["id", "name"]}
    assert result["items"] == {"Products": [{"id": "1", "name": "Apple"}, {"id": "2", "name": "Banana"}]}
    assert result["capacity"] == "2.5 KB"


def test_parse_file_to_json_from_real_file(base_path):
    file_path = base_path / "SAP_Master_data.txt"
    processor = txt_master_data_processor.MasterDataProcessor(file_path, SourceType.LOCAL)
    result = processor.parse_file_to_json()

    assert "headers" in result
    assert "items" in result
    assert "capacity" in result
    assert isinstance(result["headers"], dict)
    assert isinstance(result["items"], dict)


@patch("fastapi_celery.template_processors.master_data_processors.txt_master_data_processor.write_json_to_s3")
@patch("fastapi_celery.template_processors.master_data_processors.txt_master_data_processor.config_loader.get_config_value")
def test_upload_master_file_to_s3(mock_get_config_value, mock_write_json_to_s3):
    mock_get_config_value.return_value = "test-bucket"
    mock_write_json_to_s3.return_value = {"status": "ok"}

    processor = txt_master_data_processor.MasterDataProcessor(file_path=Path("dummy/path/file.txt"))
    processor.file_object = MagicMock()
    processor.file_object.file_name = "data_file"
    processor.file_object.file_extension = ".txt"

    result = processor._upload_master_file_to_s3(json_data={"some": "data"})

    assert result == {"status": "ok"}
    mock_get_config_value.assert_called_once_with("s3_buckets", "datahub_s3_master_data")
    mock_write_json_to_s3.assert_called_once()
