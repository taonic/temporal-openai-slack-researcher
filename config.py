from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    slack_bot_token: str
    slack_app_token: str
    slack_user_token: str
    gcp_project_id: str
    temporal_namespace: str = "default"
    temporal_api_key: str = ""
    temporal_host_port: str = "localhost:7233"
    temporal_task_queue: str = "slack-agent-task-queue"
    model_name: str = "models/gemini-2.5-flash"
    log_level: str = "INFO"
    
    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        
settings = Settings()
