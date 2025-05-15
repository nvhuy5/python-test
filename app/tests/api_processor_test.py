import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi_celery.routers.api_file_processor import router
from fastapi_celery.models.class_models import FilePathRequest
from fastapi_celery.models.class_models import StopTaskRequest
from fastapi_celery.connections.be_connection import BEConnector
from fastapi_celery.celery_worker.celery_config import celery_app

# Create a FastAPI app instance for testing
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Mock Celery task and connection to avoid Redis or RabbitMQ connection
@patch("fastapi_celery.routers.api_file_processor.celery_task.task_execute.apply_async")
@patch("celery.app.task.Task.apply_async")
@patch("kombu.connection.Connection")
def test_process_file(mock_connection, mock_apply_async, mock_apply_async_task):
    # Simulate that the task is successfully submitted without any side effects
    mock_apply_async.return_value = None
    mock_apply_async_task.return_value = None
    mock_connection.return_value = MagicMock()

    # Create request payload
    request_payload = {"file_path": "/some/path/to/file.csv"}

    # Send the POST request to the API endpoint
    response = client.post("/file/process", json=request_payload)

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert the response contains the file path and a celery_id
    response_json = response.json()
    assert "celery_id" in response_json
    assert "file_path" in response_json
    assert response_json["file_path"] == request_payload["file_path"]

    # Ensure the Celery task was called with the correct arguments
    assert mock_apply_async.called
    args, kwargs = mock_apply_async.call_args
    assert kwargs["kwargs"]["file_path"] == request_payload["file_path"]


# Mock Celery task and connection to avoid Redis or RabbitMQ connection
@patch("fastapi_celery.routers.api_file_processor.celery_task.task_execute.apply_async")
@patch("celery.app.task.Task.apply_async")
@patch("kombu.connection.Connection")
def test_process_file_failure(mock_connection, mock_apply_async, mock_apply_async_task):
    # Simulate that the task submission fails (raise an exception)
    mock_apply_async.side_effect = Exception("Task submission failed")
    mock_apply_async_task.return_value = None
    mock_connection.return_value = MagicMock()

    # Create request payload
    request_payload = {"file_path": "/some/path/to/file.csv"}

    # Send the POST request to the API endpoint
    response = client.post("/file/process", json=request_payload)

    # Assert that the response status code is 500 (Internal Server Error)
    assert response.status_code == 500

    # Assert that the response contains the error message
    response_json = response.json()
    assert "detail" in response_json
    assert "Task submission failed" in response_json["detail"]

    # Ensure the Celery task was called even though it failed
    assert mock_apply_async.called
    args, kwargs = mock_apply_async.call_args
    assert kwargs["kwargs"]["file_path"] == request_payload["file_path"]


# Mock dependencies for BEConnector and Celery control
@patch("fastapi_celery.routers.api_file_processor.celery_app.control.revoke")
@patch("fastapi_celery.routers.api_file_processor.BEConnector")
@patch("fastapi_celery.routers.api_file_processor.get_step_ids")
@patch("fastapi_celery.routers.api_file_processor.get_step_statuses")
@patch("fastapi_celery.routers.api_file_processor.get_workflow_id")
@pytest.mark.asyncio
async def test_stop_task_success(mock_get_workflow_id, mock_get_step_statuses, mock_get_step_ids, mock_BEConnector, mock_revoke):
    mock_get_workflow_id.return_value = "workflow_123"
    mock_get_step_ids.return_value = {"step1": "step_id_1"}
    mock_get_step_statuses.return_value = {"step1": "InProgress"}
    mock_BEConnector.return_value.post = MagicMock(return_value=asyncio.Future())
    mock_BEConnector.return_value.post.return_value.set_result(MagicMock(status_code=200))
    
    request_payload = {
        "task_id": "task_123",
        "reason": "Manual stop"
    }

    response = client.post("/tasks/stop", json=request_payload)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"] == "Task stopped successfully"
    assert response_json["task_id"] == "task_123"
    assert response_json["message"] == "Manual stop"

    mock_revoke.assert_called_once_with("task_123", terminate=True, signal="SIGKILL")
    mock_BEConnector.return_value.post.assert_called()


@patch("fastapi_celery.routers.api_file_processor.celery_app.control.revoke")
@patch("fastapi_celery.routers.api_file_processor.BEConnector")
@patch("fastapi_celery.routers.api_file_processor.get_step_ids")
@patch("fastapi_celery.routers.api_file_processor.get_step_statuses")
@patch("fastapi_celery.routers.api_file_processor.get_workflow_id")
@pytest.mark.asyncio
async def test_stop_task_failure(mock_get_workflow_id, mock_get_step_statuses, mock_get_step_ids, mock_BEConnector, mock_revoke):
    mock_get_workflow_id.return_value = None

    request_payload = {
        "task_id": "task_123",
        "reason": "Manual stop"
    }

    response = client.post("/tasks/stop", json=request_payload)

    assert response.status_code == 200
    response_json = response.json()
    assert "error" in response_json
    assert response_json["error"] == "Workflow ID not found for task"
    assert response_json["task_id"] == "task_123"

    mock_revoke.assert_not_called()
    mock_BEConnector.return_value.post.assert_not_called()


@patch("fastapi_celery.routers.api_file_processor.celery_app.control.revoke")
@patch("fastapi_celery.routers.api_file_processor.BEConnector")
@patch("fastapi_celery.routers.api_file_processor.get_step_ids")
@patch("fastapi_celery.routers.api_file_processor.get_step_statuses")
@patch("fastapi_celery.routers.api_file_processor.get_workflow_id")
@patch("fastapi_celery.routers.api_file_processor.logger")
@pytest.mark.asyncio
async def test_stop_task_exception_handling(mock_logger, mock_get_workflow_id, mock_get_step_statuses, mock_get_step_ids, mock_BEConnector, mock_revoke):
    # Simulate the situation where the BEConnector raises an exception
    mock_get_workflow_id.return_value = "workflow_123"
    mock_get_step_ids.return_value = {"step1": "step_id_1"}
    mock_get_step_statuses.return_value = {"step1": "InProgress"}
    mock_BEConnector.return_value.post.side_effect = Exception("Simulated BEConnector Exception")

    request_payload = {
        "task_id": "task_123",
        "reason": "Manual stop"
    }

    response = client.post("/tasks/stop", json=request_payload)

    # Assert that the response status code is 500
    assert response.status_code == 500
    response_json = response.json()
    assert response_json["status_code"] == 500
    assert "Simulated BEConnector Exception" in response_json["error"]
    mock_logger.error.assert_called_with("Failed to stop task task_123")