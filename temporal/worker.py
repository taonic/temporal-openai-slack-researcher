from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from temporalio.worker import Worker
from temporalio.contrib.openai_agents import (
    ModelActivity,
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

@asynccontextmanager
async def worker():
    client = await connect()
    with set_open_ai_agent_temporal_overrides():
        async with Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[ConversationWorkflow],
            activity_executor=ThreadPoolExecutor(100),
            activities=[
                ModelActivity().invoke_model_activity,
                get_slack_channels,
                search_slack,
                get_thread_messages,
                get_user_name,
            ],
        ) as worker:
            yield worker
