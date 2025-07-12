import logging
import secrets
from typing import List

from temporalio.common import (
    WorkflowIDConflictPolicy,
    QueryRejectCondition
)
from temporalio.client import (
    Client,
    WorkflowUpdateFailedError,
)

from temporal.conversation_workflow import (
    ConversationWorkflow,
    ProcessUserMessageInput,
)

from config import settings

class Session:
    """
    Session manages the lifecycle of an agent workflow.
    This class is responsible for starting workflows and providing
    methods to interact with them (thoughts, prompt).
    """

    def __init__(
        self,
        client: Client,
        session_id: str = None,
        task_queue: str = "slack-agent-task-queue"
    ):
        self.session_id: str = session_id if session_id else secrets.token_hex(3)
        self.client: Client = client
        self.task_queue: str = task_queue
        self.workflow_id: str = "slack_session_" + self.session_id
        self.watermark: int = 0
        
    async def start(self) -> None:
        """Start the agent workflow."""
        await self.client.start_workflow(
            ConversationWorkflow.run,
            id=self.workflow_id,
            task_queue=self.task_queue,
            id_conflict_policy=WorkflowIDConflictPolicy.USE_EXISTING
        )
        
        logging.debug('Started workflow with ID: %s', self.workflow_id)
    
    async def stop(self) -> None:
        """Stop the agent workflow."""
        if not self.workflow_id:
            raise RuntimeError("Session not started")

        handle = self.client.get_workflow_handle(self.workflow_id)
        await handle.terminate()

    async def thoughts(self) -> List[str]:
        if not self.workflow_id:
            raise RuntimeError("Session not started")
            
        handle = self.client.get_workflow_handle(self.workflow_id)
        result = await handle.query(
            ConversationWorkflow.get_chat_history,
            self.watermark
        )
        if result:
            self.watermark += len(result)
        return result

    async def prompt(self, prompt: str) -> str:
        try:
            if not self.workflow_id:
                raise RuntimeError("Session not started")

            handle = self.client.get_workflow_handle(self.workflow_id)
            input = ProcessUserMessageInput(user_input=prompt)
            result = await handle.execute_update(
                ConversationWorkflow.process_user_message,
                input,
            )
            return result
        except WorkflowUpdateFailedError:
            logging.warning("Workflow update failed, trying to fetch chat history.")
            history = await handle.query(
                ConversationWorkflow.get_chat_history,
                reject_condition=QueryRejectCondition.NOT_OPEN,
            )
            self.watermark = len(history)
            return await self.prompt(prompt)
