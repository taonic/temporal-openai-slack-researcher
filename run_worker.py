import asyncio
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.contrib.openai_agents.invoke_model_activity import ModelActivity
from temporalio.contrib.openai_agents.open_ai_data_converter import open_ai_data_converter
from temporalio.contrib.openai_agents.temporal_openai_agents import set_open_ai_agent_temporal_overrides
from temporalio.worker import Worker

from temporal.conversation_workflow import ConversationWorkflow
from research_agent.tools import get_slack_channels, search_slack, get_thread_messages, get_user_name
from config import settings

async def worker_main():
    # Configure the OpenAI Agents SDK to use Temporal activities for LLM API calls
    # and for tool calls.
    with set_open_ai_agent_temporal_overrides():
        # Create a Temporal client connected to server at the given address
        # Use the OpenAI data converter to ensure proper serialization/deserialization
        client = await Client.connect(
            "localhost:7233",
            data_converter=open_ai_data_converter,
        )

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
