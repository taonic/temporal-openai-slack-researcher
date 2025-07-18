import pytest
import uuid
import asyncio
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from temporal.workflow import ConversationWorkflow, ProcessUserMessageInput
from temporal.activities import PostToSlackInput
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio import activity
from temporalio.contrib.openai_agents import (
    ModelActivity,
)
from temporalio.contrib.openai_agents import (
    ModelActivity,
    ModelActivityParameters,
    TestModelProvider,
    set_open_ai_agent_temporal_overrides,
)
from research_agents.tools import (
    GetChannelsRequest,
)
from tests.models import (
    CombinedAgentModel
)

def get_payload(i: str, events) -> str:
    events[i].activity_task_completed_event_attributes.result.payloads[0].data.decode()


@pytest.mark.asyncio
async def test_combined_agent(client: Client):
    slack_posts: list[PostToSlackInput] = []
    
    model_activity = ModelActivity(
        TestModelProvider(
            CombinedAgentModel()
        )
    )  
    
    # Mock activities
    @activity.defn(name="post_to_slack")
    async def mock_post_to_slack(input: PostToSlackInput) -> str:
        slack_posts.append(input)
    
    @activity.defn(name="get_slack_channels")
    async def mock_get_slack_channels(request: GetChannelsRequest) -> List[Dict[str, Any]]:
        []
        
    model_params = ModelActivityParameters(start_to_close_timeout=timedelta(seconds=30))
    with set_open_ai_agent_temporal_overrides(model_params):
        async with Worker(
            client,
            task_queue=str(uuid.uuid4()),
            workflows=[ConversationWorkflow],
            activity_executor=ThreadPoolExecutor(5),
            activities=[
                model_activity.invoke_model_activity,
                mock_post_to_slack,
                mock_get_slack_channels,
            ],
        ) as worker:
            handle = await client.start_workflow(
                ConversationWorkflow.run,
                id=str(uuid.uuid4()),
                task_queue=worker.task_queue,
            )
            
            input = ProcessUserMessageInput(
                user_input="test message",
                channel_id="C123456",
                thread_ts="123.456"
            )
            
            await handle.signal(ConversationWorkflow.process_user_message, input)
            
            await asyncio.sleep(0.5)
            
            expected_messages = [
                "[view workflow](http://localhost:8233/namespaces/default/workflows",
                "final result"
            ]
            for i, message in enumerate(expected_messages, start=0):
                assert slack_posts[i].message.startswith(message)
