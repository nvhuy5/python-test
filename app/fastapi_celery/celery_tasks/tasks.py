from connections.postgres_conn import (
    get_session,
    CeleryTask
)
import traceback
from file_processors.func_mapping import *
from celery.app import Celery
from celery.result import AsyncResult
import os
from pathlib import Path

# ===
# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv(dotenv_path=f"{Path(__file__).parent.parent.parent.parent}/.env")
# ===

# celery configs
# https://docs.celeryq.dev/en/latest/userguide/configuration.html#task-track-started
celery = Celery(__name__, include=['celery_tasks.tasks'])

# Celery configuration
celery.conf.update(
    broker_url                          = os.environ.get(
        "CELERY_BROKER_URL",
        f"redis://:{os.environ.get('REDIS_PASSWORD')}@{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}/0"
    ),
    result_backend = os.environ.get(
        "CELERY_RESULT_BACKEND",
        f"db+postgresql+psycopg2://{os.environ.get('POSTGRES_USER')}:"
        f"{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:"
        f"{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"
        f"?options=--search_path%3D{os.environ.get('CELERY_SCHEMA', 'public')}"
    ),
    # use custom schema and table names for the database result backend.
    database_table_schemas              = {'task': 'celery','group': 'celery'},
    database_table_names                = {'task': 'myapp_taskmeta','group': 'myapp_groupmeta'},
    broker_connection_retry_on_startup  = True,
    task_track_started                  = True,         # To track the start of tasks
    accept_content                      = ['json'],     # We accept only json for security
    result_serializer                   = 'json',       # Serializing results in json
    timezone                            = 'UTC',        # Set your timezone
    task_serializer                     = 'json',       # Serializing tasks in json
    worker_concurrency                  = 4,            # Number of concurrent worker processes per worker (e.g., 4)
    worker_pool                         = 'prefork',    # Pool type, use 'prefork' or 'solo' or 'gevent'
    worker_prefetch_multiplier          = 1,            # Number of tasks to prefetch per worker (default: 4)
    worker_max_tasks_per_child          = 100,          # Max number of tasks a worker can process before restarting
    worker_max_memory_per_child         = 50000,        # Max memory (in KB) per worker before it is restarted
    task_acks_late                      = True,         # Acknowledge task after it’s finished (prevents tasks from being lost on crash)
)

@celery.task(bind=True)
def dummy_task(
    self,
    customer_name: str,
    task_name: str,
    task_steps: dict
) -> str:
    session = get_session()  # Get a session to interact with the database
    
    try:
        # Query to fetch the task by customer name and task name
        task_info = session.query(CeleryTask).filter_by(
            customer_name=customer_name, task_name=task_name
        ).first()
        
        if task_info is None:
            return "Task not found."

        task_info.task_status = "Started"
        task_info.task_steps = task_steps
        session.commit()  # Update the task status to "Started" and task steps

        sum_x = 0

        # Start executing the task steps
        for step in task_steps.keys():
            try:
                # Execute the step and update status
                sum_x += step_exce(function_dict.get(step), 10)  # Safely get function
                
                # Update step status to 'Pass'
                task_steps[step] = 'Pass'
                task_info.task_steps = task_steps

            except Exception as e:
                # If step fails, mark as 'Failed' and update task status to 'Failed'
                task_steps[step] = 'Failed'
                task_info.task_status = "Failed"
                task_error = {"exception": str(e), "traceback": traceback.format_exc()}
                task_info.task_steps = task_steps
                task_info.task_error = task_error
                session.commit()
                raise  # Reraise the exception after committing the error

        # If all steps pass, mark task as "Success"
        if task_info.task_status == "Started":
            task_info.task_status = "Success"
            task_info.task_result = sum_x

        session.commit()  # Final commit for task result and status

        return sum_x

    except Exception as e:
        session.rollback()  # Rollback in case of error
        task_error = {"exception": str(e), "traceback": traceback.format_exc()}
        task_info.task_status = "Failed"
        task_info.task_error = task_error
        session.commit()  # Commit the failure status and error info
        return "Task failed due to an exception."

    finally:
        session.close()  # Close the session after the operation
