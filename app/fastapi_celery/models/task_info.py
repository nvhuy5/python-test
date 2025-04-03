from pydantic import BaseModel

class TaskInfo(BaseModel):
    customer_name: str
    task_name: str
    task_id: str
    task_status: str
    task_steps: dict = {}


# Pydantic model for the request body
class StartTaskRequest(BaseModel):
    customer_name: str
    task_name: str
    # Optional: Additional task data can be passed as a dictionary
    additional_data: dict = {}


class StopTaskRequest(BaseModel):
    task_id: str
    # Optional: you can include a reason to stop the task
    reason: str = None
