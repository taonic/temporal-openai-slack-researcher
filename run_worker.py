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
from config import settings
from research_agents.tools import SlackTools

async def worker_main():
    # Configure the OpenAI Agents SDK to use Temporal activities for LLM API calls
    # and for tool calls.
    with set_open_ai_agent_temporal_overrides():
        # Create a Temporal client connected to server at the given address
        # Use the OpenAI data converter to ensure proper serialization/deserialization
        connect_args = {
            "target_host": settings.temporal_host_port,
            "data_converter": pydantic_data_converter,
        }

        if settings.temporal_api_key:
            connect_args.update({
                "namespace": settings.temporal_namespace,
                "api_key": settings.temporal_api_key,
                "tls": True,
            })

        client = await Client.connect(**connect_args)

        model_activity = ModelActivity(model_provider=None)
        worker = Worker(
            client,
            task_queue=settings.temporal_task_queue,
            workflows=[ConversationWorkflow],
            activity_executor=ThreadPoolExecutor(100),
            activities=[
                model_activity.invoke_model_activity,
                get_slack_channels,
                search_slack,
                get_thread_messages,
                get_user_name,
            ],
        )
        await worker.run()

if __name__ == "__main__":
    asyncio.run(worker_main())
