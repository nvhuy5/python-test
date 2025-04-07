from pydantic import BaseModel, field_validator
from urllib.parse import quote

class FileRequest(BaseModel):
    file_path: str

    # Pydantic field_validator for the file_path
    @field_validator('file_path', mode="after")
    def replace_backslash(cls, value):
        # Using quote to ensure the backslashes are properly escaped (URL-encoding).
        return value
