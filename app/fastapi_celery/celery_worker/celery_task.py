import sys
import traceback
import asyncio
import logging
import json
from pathlib import Path

from celery import shared_task

from .step_handler import execute_step
from connections.be_connection import BEConnector
from template_processors.file_processor import FileProcessor
from models.class_models import WorkflowModel, ApiUrl, StatusEnum, WorkflowSession, StartStep
from utils import log_helpers
import config_loader

# === Setup logging ===
logger_name = "Celery Task Execution"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)

# === Load config ===
sys.path.append(str(Path(__file__).resolve().parent.parent))

types_list = json.loads(config_loader.get_config_value("support_types", "types"))


@shared_task(bind=True)
def task_execute(self, file_path: str, celery_id: str) -> str:
    """
    Entry point Celery task (sync). Internally executes async logic using asyncio.run.
    """
    try:
        logger.info(f"[{celery_id}] Starting task execution (sync wrapper)")
        asyncio.run(handle_task(file_path, celery_id))
        return "Task completed successfully"
    except Exception as e:
        logger.exception(f"[{celery_id}] Task execution failed: {str(e)}")
        return f"Task failed: {str(e)}"


async def handle_task(file_path: str, celery_id: str):
    logger.info(f"[{celery_id}] Start processing file: {file_path}")
    file_processor = FileProcessor(file_path=file_path)
    file_processor.extract_metadata()

    body_data = {
        "filePath": file_processor.file_record["file_path_parent"],
        "fileName": file_processor.file_record["file_name"],
        "fileExtension": file_processor.file_record["file_extension"],
    }
    logger.info(f"File path ({file_path}) parsed result:\n{body_data}")
    logger.info(f"The document type of file_path - {file_path}: {file_processor.document_type}")

    # === Fetch workflow ===
    workflow = BEConnector(ApiUrl.workflow_filter, body_data=body_data)
    workflow_response = await workflow.post()
    if not workflow_response:
        logger.error(f"[{celery_id}] Failed to fetch workflow for file: {file_path}")
        return
    logger.info(f"Workflow details:\n{workflow_response}")
    workflow_model = WorkflowModel(**workflow_response)

    # === Start session ===
    session_connector = BEConnector(ApiUrl.workflow_session_start, {
        "workflowId": workflow_model.id,
        "celeryId": celery_id,
        "filePath": file_path,
    })
    session_response = await session_connector.post()
    if not session_response:
        logger.error(f"[{celery_id}] Failed to create workflow session.")
        return
    logger.info(f"Session details:\n{session_response}")
    workflow_session = WorkflowSession(**session_response)

    # === Init context ===
    context = {
        "input_data": None,
        "file_path": file_path,
        "celery_id": celery_id,
    }

    # === Process steps ===
    for step in workflow_model.workflowSteps:
        logger.info(f"[{celery_id}] Starting step: {step.stepName}")

        # Start step
        step_response = await BEConnector(ApiUrl.workflow_step_start, {
            "sessionId": workflow_session.id,
            "stepId": step.workflowStepId
        }).post()
        step_response_model = StartStep(**step_response)

        # Execute step (context is updated internally)
        await execute_step(file_processor, step, context, celery_id)

        # Finish step
        step_output = (
            f"{context['materialized_step_data_loc']}/{file_processor.file_record['file_name'].rsplit('.', 1)[0]}.json"
            if context['materialized_step_data_loc']
            else None
        )
        await BEConnector(ApiUrl.workflow_step_finish, {
            "workflowHistoryId": step_response_model.workflowHistoryId,
            "code": StatusEnum.SUCCESS,
            "message": "",
            "dataInput": "input_data",
            "dataOutput": step_output,
        }).post()

    # === Finish session ===
    await BEConnector(ApiUrl.workflow_session_finish, {
        "id": workflow_session.id,
        "code": StatusEnum.SUCCESS,
        "message": ""
    }).post()

    file_processor.write_raw_to_s3(file_path)

    logger.info(f"[{celery_id}] Finished processing file: {file_path}")
