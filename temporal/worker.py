from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker
from config import settings
from temporal.workflow import ConversationWorkflow
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
    async with Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[ConversationWorkflow],
        activity_executor=ThreadPoolExecutor(100),
        interceptors=[TracingInterceptor()],
        activities=[
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
