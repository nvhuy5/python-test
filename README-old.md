# Docker Compose
```bash
# Install
sudo curl -L "https://github.com/docker/compose/releases/download/`curl -fsSLI -o /dev/null -w %{url_effective} https://github.com/docker/compose/releases/latest | sed 's#.*tag/##g' && echo`/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose
```

```bash
docker-compose up -d

# rebuild
docker-compose up -d --build --force-recreate
docker-compose up --build --force-recreate --no-deps
```

- Remove all running containers
```bash
# Stop and remove everything
docker-compose down -v --remove-orphans
# Remove dangling volumes
docker volume prune -f
# Verify no volumes remain
docker volume ls
# Start fresh
docker-compose up -d
```

```bash
# remove all containers
docker rm $(docker ps -a -q) -f
# remove all images
docker rmi $(docker images -a -q)
docker rmi $(docker ps -a | grep -v "redis\|mongo\|mongo-express" | awk 'NR>1 {print $1}')

# prune all stopped containers
docker container prune

# prune all volumes
docker volume prune --all
docker system prune -a --volumes
docker-compose down --volumes --rmi all --remove-orphans

docker builder prune

# stop
docker stop $(docker ps -a -q)
```

- To access the FastAPI docs
    - http://localhost:8000/docs#/
    
# Docker Secrets
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

# Docker .env
```txt
COMPOSE_PROJECT_NAME=my_custom_project
POSTGRES_DB=celery
CELERY_SCHEMA=celery
POSTGRES_USER=admin
POSTGRES_PASSWORD=12345678
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_PASSWORD=12345678
REDIS_HOST=redis
REDIS_PORT=6380
APP_PORT=8000
FLOWER_PORT=5555
CELERY_CONCURRENCY=4
CELERY_POOL=prefork
CELERY_MAX_TASKS_PER_CHILD=100
CELERY_MAX_MEMORY_PER_CHILD=50000
CELERY_MIN_PROCESSES=2
CELERY_MAX_PROCESSES=10
```
**NOTES: `COMPOSE_PROJECT_NAME=my_custom_project` will provide information for project name `"com.docker.compose.project"`**


# Connect PostgreSQL
- Connect database
```bash
docker exec -it <DOCKER-IMAGE-ID> bash
psql -h localhost -p 5432 -U ${POSTGRES_USER} -d ${POSTGRES_DB}
# Or
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

- Get all tables
```bash
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
\dt
# To view tables from specific schema
\dt schema_name.*
```

- To retrieve all tables
```bash
docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
SELECT * FROM celery_tasks; # must include the semicolon (;) at the end of the query
```

- To fix LF error for sh script
```bash
sed -i 's/\r//g' init-users.sh
```

# ===
Note for the Test and Prod environments
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

