import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, model_validator
from enum import Enum
import config_loader


# === Source Type Enum ===
class SourceType(str, Enum):
    LOCAL = "local"
    S3 = "s3"


class DocumentType(str, Enum):
    MASTER_DATA = "master_data"
    ORDER = "order"


class StatusEnum(str, Enum):
    SUCCESS = "1"
    FAILED = "2"
    SKIPPED = "3"
    PROCESSING = "4"


class ApiUrl(str, Enum):
    workflow_filter = f"{config_loader.get_env_variable('BASE_API_URL', '')}/api/workflow/filter"
    workflow_session_start = f"{config_loader.get_env_variable('BASE_API_URL', '')}/api/workflow/session/start"
    workflow_session_finish = f"{config_loader.get_env_variable('BASE_API_URL', '')}/api/workflow/session/finish"
    workflow_step_start = f"{config_loader.get_env_variable('BASE_API_URL', '')}/api/workflow/step/start"
    workflow_step_finish = f"{config_loader.get_env_variable('BASE_API_URL', '')}/api/workflow/step/finish"


class StopTaskRequest(BaseModel):
    task_id: str
    reason: str | None = None


class FilePathRequest(BaseModel):
    file_path: str


class WorkflowStep(BaseModel):
    workflowStepId: str
    stepName: str
    stepOrder: int
    stepConfiguration: List[dict] = []


class WorkflowModel(BaseModel):
    id: str
    name: str
    workflowSteps: List[WorkflowStep]


class WorkflowSession(BaseModel):
    id: str
    status: str


class StartStep(BaseModel):
    workflowHistoryId: str
    status: str


class PathEncoder(json.JSONEncoder):  # pragma: no cover  # NOSONAR
    def default(self, obj):
        if isinstance(obj, Path):
            return obj.as_posix()
        return super().default(obj)


class StepDefinition(BaseModel):  # pragma: no cover  # NOSONAR
    function_name: str
    data_input: Optional[str] = None
    data_output: Optional[str] = None
    store_materialized_data: bool = False
    extract_to: Dict[str, str] = {}
    args: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_constraints(cls, values):
        if values.store_materialized_data and not values.data_output:
            raise ValueError("'store_materialized_data' requires 'data_output' to be set")
        return values
