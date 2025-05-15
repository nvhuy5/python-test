# Standard Library Imports
import logging
from utils import log_helpers
import importlib
import inspect
import types
from models.class_models import StepDefinition

# ===
# Set up logging
logger_name = "File Procesor Routers"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

WORKFLOW_MODULES = [
    "extract_metadata",
    "mapping",
    "parse_file_to_json",
    "publish_data",
    "validation",
    "write_json_to_s3",
    "write_raw_to_s3"
]

STEP_DEFINITIONS = {
    "file_parse": StepDefinition(
        function_name="parse_file_to_json",
        data_input=None,
        data_output="parsed_data",
        extract_to={"po_data": "po_data"},
        # Write data to S3 after the step
        store_materialized_data=True
    ),
    "mapping": StepDefinition(
        function_name="mapping",
        data_output="mapped_data"
    ),
    "validation": StepDefinition(
        function_name="validation",
        data_input=None,
        data_output="validated_data"
    ),
    "write_json_to_s3": StepDefinition(
        function_name="write_json_to_s3",
        data_input="parsed_data",
        data_output="s3_result"
    ),
    "publish_data": StepDefinition(
        function_name="publish_data"
    ),
}

class FileProcessor:
    """
    Loads modules defined in the `workflow_nodes` package.

    Each function name in WORKFLOW_MODULES corresponds to a Python file in the `workflow_nodes/` directory, such as:
    - `extract_metadata` -> `workflow_nodes/extract_metadata.py`
    - `mapping` -> `workflow_nodes/mapping.py`
    - `parse_file_to_json` -> `workflow_nodes/parse_file_to_json.py`
    - etc.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_record = {}
        self.source_type = None
        self.document_type = None
        
        self._register_workflow_functions()

    def _register_workflow_functions(self):
        base_module = "template_processors.workflow_nodes"

        for module_name in WORKFLOW_MODULES:
            try:
                module = importlib.import_module(f"{base_module}.{module_name}")
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    bound_method = types.MethodType(func, self)
                    setattr(self, name, bound_method)
                    logger.debug(f"Registered method: {name} from {module_name}")
            except ModuleNotFoundError:
                logger.warning(f"Module {module_name} not found in workflow_nodes.")
