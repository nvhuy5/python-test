import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi_celery.celery_worker.celery_task import task_execute, handle_task
from fastapi_celery.models.class_models import StartStep

# === Test for task_execute ===
@patch("fastapi_celery.celery_worker.celery_task.handle_task", new_callable=AsyncMock)
def test_task_execute_success(mock_handle_task):
    result = task_execute(file_path="test/path.pdf", celery_id="123-abc")
    assert result == "Task completed successfully"
    mock_handle_task.assert_awaited_once_with("test/path.pdf", "123-abc")

@patch("fastapi_celery.celery_worker.celery_task.handle_task", new_callable=AsyncMock)
def test_task_execute_failure(mock_handle_task):
    mock_handle_task.side_effect = Exception("Boom!")
    result = task_execute(file_path="test/path.pdf", celery_id="123-abc")
    assert "Task failed: Boom!" in result
    mock_handle_task.assert_awaited_once()

# === Test for handle_task ===
@pytest.mark.asyncio
@patch("fastapi_celery.celery_worker.celery_task.FileProcessor")
@patch("fastapi_celery.celery_worker.celery_task.BEConnector")
@patch("fastapi_celery.celery_worker.celery_task.StartStep")
@patch("fastapi_celery.celery_worker.celery_task.execute_step", new_callable=AsyncMock)
@patch("fastapi_celery.celery_worker.celery_task.config_loader.get_config_value")
async def test_handle_task_success(mock_config, mock_execute_step, mock_start_step, mock_be_connector, mock_file_processor):
    # Mocking config and file processing behavior
    mock_config.side_effect = lambda section, key: {
        "converted_files": "test-bucket",
        "materialized_step_data_loc": "materialized/data/path"
    }.get(key, "[]")

    mock_instance = MagicMock()
    mock_instance.file_record = {
        "file_path_parent": "parent/path",
        "file_name": "file.pdf",
        "file_extension": ".pdf"
    }
    mock_file_processor.return_value = mock_instance

    # Mocking workflow and session responses
    workflow_resp = {
        "id": "workflow-1",
        "name": "Test Workflow",
        "workflowSteps": [
            {"stepName": "Step A", "workflowStepId": "step-1", "stepOrder": 1, "stepConfiguration": []},
            {"stepName": "Step B", "workflowStepId": "step-2", "stepOrder": 2, "stepConfiguration": []}
        ]
    }
    session_resp = {
        "id": "session-1",
        "status": "started"
    }

    # This mimics StartStep(**step_response)
    step_start_1 = {"workflowHistoryId": "history-1", "status": "started"}
    step_start_2 = {"workflowHistoryId": "history-2", "status": "started"}

    # Ensuring you mock every step correctly (e.g. workflow + session starts/ends + step starts/finishes)
    be_mock = AsyncMock()
    be_mock.post.side_effect = [workflow_resp, session_resp, step_start_1, {}, step_start_2, {}, {}]
    mock_be_connector.return_value = be_mock

    mock_execute_step.return_value = {"result": "output"}

    # Pydantic StartStep model instantiation
    def side_effect_start_step(**kwargs):
        return StartStep(**kwargs)

    mock_start_step.side_effect = side_effect_start_step
    
    def side_effect_execute_step(file_processor, step, context, celery_id):
        # Ensure 'materialized_step_data_loc' is in context
        context['materialized_step_data_loc'] = 'materialized/data/path'
        return {"result": "output"}
    
    mock_execute_step.side_effect = side_effect_execute_step

    # Call the task handler and await the result
    await handle_task("test/path/file.pdf", "celery-123")

    # Verify the correct number of calls
    print(f"BEConnector post calls: {be_mock.post.call_count}")
    assert be_mock.post.call_count == 7
    assert mock_execute_step.await_count == 2

@pytest.mark.asyncio
@patch("fastapi_celery.celery_worker.celery_task.FileProcessor")
@patch("fastapi_celery.celery_worker.celery_task.BEConnector")
@patch("fastapi_celery.celery_worker.celery_task.config_loader.get_config_value")
async def test_handle_task_no_workflow(mock_config, mock_be_connector, mock_file_processor):
    mock_config.side_effect = lambda section, key: "test-bucket"

    mock_instance = MagicMock()
    mock_instance.file_record = {
        "file_path_parent": "parent/path",
        "file_name": "file.pdf",
        "file_extension": ".pdf"
    }
    mock_file_processor.return_value = mock_instance

    be_mock = AsyncMock()
    be_mock.post.return_value = None
    mock_be_connector.return_value = be_mock

    await handle_task("some/path.pdf", "celery-456")

    assert be_mock.post.await_count == 1

@pytest.mark.asyncio
@patch("fastapi_celery.celery_worker.celery_task.FileProcessor")
@patch("fastapi_celery.celery_worker.celery_task.BEConnector")
@patch("fastapi_celery.celery_worker.celery_task.config_loader.get_config_value")
async def test_handle_task_session_fail(mock_config, mock_be_connector, mock_file_processor):
    mock_config.side_effect = lambda section, key: "test-bucket"

    mock_instance = MagicMock()
    mock_instance.file_record = {
        "file_path_parent": "parent/path",
        "file_name": "file.pdf",
        "file_extension": ".pdf"
    }
    mock_file_processor.return_value = mock_instance

    workflow_resp = {
        "id": "workflow-1",
        "name": "Test Workflow",
        "workflowSteps": []
    }

    be_mock = AsyncMock()
    be_mock.post.side_effect = [workflow_resp, None]
    mock_be_connector.return_value = be_mock

    await handle_task("file.pdf", "celery-999")
    assert be_mock.post.await_count == 2
