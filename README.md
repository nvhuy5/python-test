# Updating notes
- Apr 01,2025:
    - Create some functions for handling PDF file
    - Update to using Async mechanism
    - Update requirement libraries
        - `celery[postgres]` -> `celery[sqlalchemy]`: celery 5.4.0 does not provide the extra `postgresql`
        - `psycopg2-binary` -> `asyncpg`: use for async mechanism
        - remove `pymongo` library from the packages

- Apr 03, 2025:
    - Modify the code following the new workflow
    ![image](./DataHub%20workflow.png)
    - Add MinIO to the architecture

# Useful commands for Docker and Docker Compose
## Docker Compose
- Remove all running containers and attached volumes
```bash
# Stop and remove everything
sudo docker-compose down --volumes --rmi all --remove-orphans
sudo docker rm $(sudo docker ps -a -q) -f
# remove all images
sudo docker rmi $(sudo docker images -a -q)
# prune all volumes
sudo docker volume prune --all
sudo docker system prune -a --volumes
```

- Rebuild
```bash
# rebuild
sudo docker-compose up -d --build --force-recreate
sudo docker-compose up --build --force-recreate --no-deps
```

## Docker Secrets
- Must enable the Docker Swarm
```bash
# Get Docker Swarm info
sudo docker info | grep Swarm

# Init Docker Swarm
sudo docker swarm init
```

- Create Docker Secrets
```bash
echo "mypassword" | sudo docker secret create mongo_password -

# Get all Docker secrets
sudo docker secret ls
```

## Docker .env content
```txt
COMPOSE_PROJECT_NAME=my_custom_project
POSTGRES_DB=celery
CELERY_SCHEMA=celery
POSTGRES_USER=admin
POSTGRES_PASSWORD=12345678
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_PASSWORD=12345678
REDIS_HOST=localhost
REDIS_PORT=6379
APP_PORT=8000
FLOWER_PORT=5555
CELERY_CONCURRENCY=4
CELERY_POOL=prefork
CELERY_MAX_TASKS_PER_CHILD=100
CELERY_MAX_MEMORY_PER_CHILD=50000
CELERY_MIN_PROCESSES=2
CELERY_MAX_PROCESSES=10
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_PORT=19000
MINIO_CONSOLE_PORT=19001
S3_ACCESS_KEY=
S3_ACCESS_SECRET=
```
**NOTES: `COMPOSE_PROJECT_NAME=my_custom_project` will provide information for project name `"com.docker.compose.project"`**


## Connect to PostgreSQL database
- Connect database
```bash
sudo docker exec -it <DOCKER-IMAGE-ID> bash
psql -h localhost -p 5432 -U ${POSTGRES_USER} -d ${POSTGRES_DB}
# Or
sudo docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

- Get all tables
```bash
sudo docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
\dt
# To view tables from specific schema
\dt schema_name.*
```

- To retrieve all tables
```bash
sudo docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
SELECT * FROM celery_tasks; # must include the semicolon (;) at the end of the query
```

- To fix LF error for sh script
```bash
sed -i 's/\r//g' init-users.sh
```

## Note for the Test and Prod environments
Using python-decouple Library
Another option is to use the python-decouple library, which provides a cleaner way to handle environment variables. It also allows you to define default values and load them only when needed, which can help prevent loading .env files in production.

Install it with:
```bash
pip install python-decouple
```
Then, use Config to load environment variables:
Example with python-decouple:
```python
from decouple import Config, Csv

config = Config()

# Load environment variables
DATABASE_URL = config('DATABASE_URL', default='default_db_url')
SECRET_KEY = config('SECRET_KEY', default='default_secret')

print(f"DATABASE_URL: {DATABASE_URL}")
print(f"SECRET_KEY: {SECRET_KEY}")
```

With this, you can store your environment variables in the .env file and load them using python-decouple, or use system environment variables if they exist.

- In test environments, you would have .env loaded with your test credentials.
- In production environments, you could rely on system environment variables instead of loading .env.


## How to use unittest
```bash
# Specificaly test for one function
python -m unittest tests.ext_detection.TestExtDetection.test_valid_extension

# To test for all functions in `ext_detection.py` module
python -m unittest tests.ext_detection
```

## Force close all uvicorn task running
```bash
tasklist | findstr uvicorn
taskkill /PID <PID> /F
```