import time
import traceback
import logging
from utils import helpers

from fastapi import APIRouter
from sqlalchemy.exc import SQLAlchemyError
from connections.postgres_conn import (
    get_session,  # Assuming this provides SQLAlchemy sessions
    CeleryTask,  # This should be the CeleryTask model
    MappingRules  # This should be the MappingRule model
)
from celery_tasks import tasks as celery_task
from models import task_info

# ===
# Set up logging
logger_name = 'FastAPI'  # You can give your logger any name you prefer
helpers.logging_config(logger_name)  # Apply the logging configuration
logger = logging.getLogger(logger_name)  # Get the logger instance
# ===

router = APIRouter()

# Submit a task
@router.post("/start", summary="Start a new task")
def start(request: task_info.StartTaskRequest):
    try:
        # task_name + timestamp
        task_name = f'{request.customer_name.lower()}_{request.task_name}_{time.time_ns()}'
        session = get_session()  # Get a session to interact with the DB
        logger.debug(f"Starting task creation for {task_name}")
        
        # Initialize task info and task steps
        task_info = {}
        task_steps = {}

        # Get the mapping rule for the customer (use SQLAlchemy instead of MongoDB)
        mapping_rule = session.query(MappingRules).filter_by(customer_name=request.customer_name).first()
        
        if mapping_rule is None:
            raise ValueError(f"No mapping rule found for customer: {request.customer_name}")

        # Create task steps based on the mapping rule
        # Assuming rules are stored in a JSON column
        for step in mapping_rule.rules:
            task_steps[step] = 'Pending'
        
        # Submit task (the task submission logic remains the same as before)
        task_submit = celery_task.dummy_task.delay(
            request.customer_name,
            task_name,
            task_steps
        )
        
        # Set up task info for insertion into PostgreSQL
        task_info["task_id"] = task_submit.task_id
        task_info["customer_name"] = request.customer_name
        task_info["task_name"] = task_name
        task_info["task_status"] = task_submit.status
        task_info["task_steps"] = str(task_steps)  # Convert task_steps to string for PostgreSQL (JSON, Text, etc.)
        
        # Insert task info into PostgreSQL (using SQLAlchemy)
        task_record = CeleryTask(
            task_id=task_info["task_id"],
            customer_name=task_info["customer_name"],
            task_name=task_info["task_name"],
            task_status=task_info["task_status"],
            task_steps=task_info["task_steps"]
        )
        
        session.add(task_record)  # Add the task record to the session
        session.commit()  # Commit the transaction
        session.close()  # Close the session

        # Return the task info in the response
        return {
            'customer_name': task_info.get('customer_name'),
            'task_name': task_info.get('task_name'), 
            'task_id': task_info.get('task_id'), 
            'status': task_info.get('task_status'),
            'additional_data': request.additional_data  # Store additional data
        }

    except Exception as e:
        # Handle any exceptions gracefully and log the error for debugging
        traceback.print_exc()
        return {"error": str(e)}


# check status a task
@router.get(
    "/status/{customer_name}/{task_name}",
    summary="Get task by `customer_name` and `task_name`"
)
def status(customer_name: str, task_name: str):
    # Get a new session instance to interact with the database
    session = get_session()
    
    try:
        # Query to find tasks matching the customer_name and task_name
        task_status = session.query(CeleryTask).filter(
            CeleryTask.customer_name == customer_name,
            CeleryTask.task_name.ilike(f"%{task_name}%")  # Case-insensitive search using 'ilike'
        ).all()  # Fetch all matching tasks

        if task_status:
            # Convert result to a list of dicts (optional step depending on your preference)
            result = [
                {
                    "task_id": task.task_id,
                    "customer_name": task.customer_name,
                    "task_name": task.task_name,
                    "task_status": task.task_status,
                    "task_steps": task.task_steps
                }
                for task in task_status
            ]
            return result
        else:
            return {"message": "Task not found"}
    
    except Exception as e:
        # Handle any database-related errors
        return {"error": str(e)}
    
    finally:
        # Close the session after the operation
        session.close()

# stop a stask
@router.post(
    "/stop",
    summary="Stop a running task by providing the task_id",
    description="""
### Stop a running Task

This endpoint stops a running task. You can specify the task details in the request body.

**Parameters:**
- `task_id`: The running task id
- `reason`: Stop reason (optional).

**Example request:**
```json
{
    "task_id": "1234",
    "reason": "stop"
}
```
"""
)
def stop(request: task_info.StopTaskRequest):
    # Get a new session instance to interact with the database
    session = get_session()

    try:
        # Query the task using task_id
        task_info = session.query(CeleryTask).filter(CeleryTask.task_id == request.task_id).first()

        # Check if task exists
        if not task_info:
            return {"message": "Task not found"}

        # Check if the task is still running (not 'Success' or 'Failed')
        if task_info.task_status not in ['Success', 'Failed']:
            try:
                # Stop the task using Celery's revoke method (send a SIGKILL signal)
                celery_task.celery.control.revoke(request.task_id, terminate=True, signal="SIGKILL")
                
                # Update the task status to 'Stopped'
                task_info.task_status = "Stopped"
                
                # Commit the changes to the database
                session.commit()
                
                return {
                    'customer_name': task_info.customer_name,
                    'task_name': task_info.task_name,
                    'task_id': request.task_id,
                    'status': 'Stopped',
                    'reason': request.reason
                }
            except Exception as e:
                # Handle exceptions when stopping the task
                return {
                    "message": "Failed to stop the task",
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
        else:
            # Cannot stop tasks that are already done
            return {"message": "Task has been completed or failed, cannot stop"}

    except SQLAlchemyError as e:
        # Handle SQLAlchemy errors
        return {
            "message": "Database error occurred",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
    finally:
        # Close the session after the operation
        session.close()