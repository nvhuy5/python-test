import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
from typing import Any

from fastapi_celery.celery_worker.celery_task import execute_step
from fastapi_celery.models.class_models import WorkflowStep


class TestExecuteStep(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_file_processor = MagicMock()
        self.data_input = {"key": "value"}
        self.mock_step = WorkflowStep(
            workflowStepId="step1",
            stepName="file_parse",
            stepOrder=1,
            stepConfiguration=[]
        )

    async def test_execute_step_with_coroutine_method_and_no_input(self):
        self.mock_step.stepName = "file_parse"
        self.mock_file_processor.parse_file_to_json = AsyncMock(return_value="parsed_data")

        mock_context = {}
        mock_task_id = "test-task-id"
        result = await execute_step(self.mock_file_processor, self.mock_step, mock_context, mock_task_id)
        self.assertEqual(result, "parsed_data")
        self.mock_file_processor.parse_file_to_json.assert_awaited_once()

    async def test_execute_step_with_coroutine_method_and_input(self):
        self.mock_step.stepName = "validation"
        self.mock_file_processor.validation = AsyncMock(return_value="validated_data")

        mock_context = {"input_data": "some_input"}
        mock_task_id = "test-task-id"

        result = await execute_step(self.mock_file_processor, self.mock_step, mock_context, mock_task_id)

        self.assertEqual(result, "validated_data")
        self.mock_file_processor.validation.assert_awaited_once_with()

    async def test_execute_step_with_sync_method_and_input(self):
        self.mock_step.stepName = "write_json_to_s3"
        self.mock_file_processor.write_json_to_s3 = MagicMock(return_value="written")

        mock_task_id = "test-task-id"
        context = {"input_data": {"key": "value"}}
        result = await execute_step(self.mock_file_processor, self.mock_step, context, mock_task_id)

        self.assertEqual(result, "written")
        self.mock_file_processor.write_json_to_s3.assert_called_once_with(None)

    async def test_execute_step_with_missing_method(self):
        self.mock_step.stepName = "non_existent_method"
        setattr(self.mock_file_processor, "non_existent_method", None)

        mock_task_id = "test-task-id"
        result = await execute_step(self.mock_file_processor, self.mock_step, self.data_input, mock_task_id)

        self.assertIsNone(result)

    async def test_execute_step_raises_exception_in_method(self):
        self.mock_step.stepName = "file_parse"
        self.mock_file_processor.parse_file_to_json = AsyncMock(side_effect=RuntimeError("Boom"))
        
        mock_context = {}
        mock_task_id = "test-task-id"
        result = await execute_step(self.mock_file_processor, self.mock_step, mock_context, mock_task_id)
        self.assertIsNone(result)
