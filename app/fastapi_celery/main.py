from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from connections.postgres_conn import *
from routers import tasks
from startup import init_mapping_rules


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_mapping_rules()
    yield
    # Shutdown logic


app = FastAPI(lifespan=lifespan)
app.include_router(tasks.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
