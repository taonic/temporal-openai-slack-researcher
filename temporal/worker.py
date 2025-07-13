from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import timedelta

from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker
from temporalio.contrib.openai_agents import (
    ModelActivity,
    ModelActivityParameters,
    set_open_ai_agent_temporal_overrides,
)
from config import settings
from temporal.conversation_workflow import ConversationWorkflow
from temporal.client import connect
from research_agents.tools import (
    get_slack_channels,
    search_slack,
    get_thread_messages,
    get_user_name,
)
from temporal.activities import (
    post_to_slack,
)

@asynccontextmanager
async def worker():
    client = await connect()
    with set_open_ai_agent_temporal_overrides(
        model_params=ModelActivityParameters(
            schedule_to_close_timeout=None,
            start_to_close_timeout=timedelta(seconds=60),
        ),
    ):
        async with Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[ConversationWorkflow],
            activity_executor=ThreadPoolExecutor(100),
            interceptors=[TracingInterceptor()],
            activities=[
                ModelActivity().invoke_model_activity,
                # tool activities
                get_slack_channels,
                search_slack,
                get_thread_messages,
                get_user_name,
                # vanilla activities
                post_to_slack,
            ],
        ) as worker:
            yield worker
