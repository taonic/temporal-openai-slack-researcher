import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.openai_agents import (
    ModelActivity,
    set_open_ai_agent_temporal_overrides,
)
from temporalio.contrib.pydantic import pydantic_data_converter

from temporal.conversation_workflow import ConversationWorkflow
from research_agents.tools import (
    get_slack_channels,
    search_slack,
    get_thread_messages,
    get_user_name,
)
from slack.message_handler import MessageHandler
from slack.session_manager import SessionManager
from config import settings

async def main():
    connect_args = {
        "target_host": settings.temporal_host_port,
        "data_converter": pydantic_data_converter,
        "namespace": settings.temporal_namespace,
    }

    if settings.temporal_api_key:
        connect_args.update({
            "api_key": settings.temporal_api_key,
            "tls": True,
        })

    client = await Client.connect(**connect_args)
    
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
        ):
            async with SessionManager(client=client) as manager:
                await MessageHandler(manager).start()

if __name__ == "__main__":
    asyncio.run(main())
