from pydantic_settings import BaseSettings
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import os

class Settings(BaseSettings):
    # Slack settings
    slack_bot_token: str
    slack_app_token: str
    slack_user_token: str

    # Temporal settings
    temporal_namespace: str = "default"
    temporal_api_key: str = ""
    temporal_host_port: str = "localhost:7233"
    temporal_ui_url: str = "http://localhost:8233"
    temporal_task_queue: str = "slack-agent-task-queue"
    temporal_codec_key: bytes = "" # must be 32 bytes
    temporal_enable_telemetry: bool = False

    # LLM settings
    model_name: str = "gpt-4o"
    eval_model_name: str = "gpt-4o"
    research_mode: str = "with_judge"

    # Misc
    log_level: str = "INFO"
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "temporal-openai-slack-researcher"
    
    class Config:
        extra = "ignore"
        env_file = os.getenv("ENV_FILE", ".env")
        
settings = Settings()
