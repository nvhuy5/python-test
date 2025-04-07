import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from connections.postgres_conn import *
from routers import tasks, file_processor
from startup import init_mapping_rules

# ===
# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv(dotenv_path=f"{Path(__file__).parent.parent.parent}/.env")
# ===

# Define the lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_mapping_rules()
    # Application runs here, during this time the app is alive
    yield
    # Shutdown logic can go here if needed (after `yield`)

# Create the FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(tasks.router)
app.include_router(file_processor.router)

# Run the app with uvicorn (only when this script is executed directly)
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get('APP_PORT', 8000))
    )
