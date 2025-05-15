import logging
import asyncio
from typing import Any
from template_processors.file_processor import FileProcessor, STEP_DEFINITIONS
from models.class_models import WorkflowStep
from utils import log_helpers
import config_loader

# ===
# Set up logging
logger_name = "Step Handler"
log_helpers.logging_config(logger_name)
logger = logging.getLogger(logger_name)
# ===

def has_args(step_config):
    return hasattr(step_config, "args") and step_config.args

def resolve_args(step_config, context, step_name):
    if has_args(step_config):
        args = [context[arg] for arg in step_config.args]
        logger.info(f"[resolve_args] using args for {step_name}: {step_config.args}")
        context["input_data"] = args[0] if len(args) == 1 else args
    elif step_config.data_input:
        args = [context.get(step_config.data_input)]
        logger.info(f"[resolve_args] using {args} for {step_name}")
    else:
        args = []
    return args

async def execute_step(file_processor: FileProcessor, step: WorkflowStep, context: dict, task_id: str):
    step_name = step.stepName
    logger.info(f"Executing step: {step_name}")

    try:
        step_config = STEP_DEFINITIONS.get(step_name)
        if not step_config:
            raise ValueError(f"No step configuration found for step '{step_name}'.")

        method_name = step_config.function_name
        method = getattr(file_processor, method_name, None)

        if method is None or not callable(method):
            raise AttributeError(f"Function '{method_name}' not found in FileProcessor.")

        # Resolve args
        args = resolve_args(step_config, context, step_name)
        logger.info(f"Calling {method_name} with args: {args}")

        # Call method (await if coroutine)
        result = await method(*args) if asyncio.iscoroutinefunction(method) else method(*args)
        logger.info(f"Step '{step_name}' executed successfully.")

        # Save output
        output_key = step_config.data_output
        if output_key:
            context[output_key] = result
            context["input_data"] = result

        # Extract specific subfields into context for further usage
        extract_map = step_config.extract_to or {}
        logger.info(f"Extracted map for further usage: {extract_map}")
        for ctx_key, result_key in extract_map.items():
            try:
                context[ctx_key] = result
            except Exception as extract_err:
                logger.warning(f"Failed to extract '{result_key}' to context['{ctx_key}']: {extract_err}")

        # Handle logic to store materialized data after every step
        # Reset the materialized_step_data_loc every step
        context["materialized_step_data_loc"] = None
        if step_config.store_materialized_data:
            materialized_step_data_loc = config_loader.get_config_value("s3_buckets", "materialized_step_data_loc")
            s3_key_prefix = f"{materialized_step_data_loc}/{task_id}/{step_name}"
            context["materialized_step_data_loc"] = s3_key_prefix
            file_processor.write_json_to_s3(result, s3_key_prefix=s3_key_prefix)

        return result

    except AttributeError as e:
        logger.error(f"[Missing step]: {str(e)}")
        return None
    except Exception as e:
        logger.exception(f"Exception during step '{step_name}': {str(e)}")
        return None
