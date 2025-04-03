# db_connection.py

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Text, JSON

# ===
# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv(dotenv_path='../../.env')
# ===

# Setup SQLAlchemy Base and session
Base = declarative_base()
SCHEMA_NAME = os.environ.get('CELERY_SCHEMA', 'public')  # Default to 'public' if not set

# Define the task table as a Python class (ORM model)
class CeleryTask(Base):
    __tablename__ = 'celery_tasks'
    __table_args__ = {'schema': SCHEMA_NAME}
    
    task_id = Column(String(255), primary_key=True)  # task_id should be unique (no auto-increment)
    customer_name = Column(String(255))
    task_name = Column(String(255))
    task_status = Column(String(50))
    # If task_steps is a JSON, consider changing to Column(JSON)
    # task_steps = Column(Text)
    task_steps = Column(JSON)

    def __repr__(self):
        return f"<CeleryTask(task_id={self.task_id}, task_name={self.task_name}, status={self.task_status})>"

class MappingRules(Base):
    __tablename__ = 'mapping_rules'
    __table_args__ = {'schema': SCHEMA_NAME}

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(255))
    rules = Column(JSON)  # Assuming 'rules' is stored as a JSON column

    def __repr__(self):
        return f"<MappingRule(customer_name={self.customer_name}, rules={self.rules})>"

# Create the engine to connect to PostgreSQL
DATABASE_URL = os.environ.get(
    "POSTGRES_URL",
    f"postgresql://{os.environ.get('POSTGRES_USER')}:"
    f"{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:"
    f"{os.environ.get('POSTGRES_PORT')}/{os.environ.get('POSTGRES_DB')}"
)
engine = create_engine(
    DATABASE_URL,
    connect_args={'options': f'-csearch_path={SCHEMA_NAME},public'}
)

# Create all tables (if they don't already exist)
# The checkfirst=True parameter makes SQLAlchemy check if the table exists before attempting to create it.
Base.metadata.create_all(engine, checkfirst=True)

# Create a session factory to interact with the database
Session = sessionmaker(bind=engine)

def get_session():
    """Function to get a new session instance"""
    return Session()

def insert_task_info(request, task_name, task_submit, task_steps):
    # Get a new session instance
    session = get_session()
    
    try:
        # Create a new task entry
        task_info = CeleryTask(
            task_id=task_submit.task_id,  # Use the task_id from Celery
            customer_name=request.customer_name,
            task_name=task_name,
            task_status=task_submit.status,
            task_steps=task_steps
        )
        
        # Add task info to the session and commit the transaction
        session.add(task_info)
        session.commit()
        
        print("Task info inserted into Postgres via SQLAlchemy.")
    
    except Exception as e:
        print(f"Error inserting task info: {e}")
        session.rollback()  # Rollback the transaction in case of error
    finally:
        # Close the session after the operation
        session.close()
