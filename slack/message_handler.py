import logging
from typing import List, Dict

from slack_bolt.async_app import AsyncApp
from slack_bolt import SetStatus, Say, SetSuggestedPrompts
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from temporalio.client import Client

from config import settings
from temporal.workflow import (
    ConversationWorkflow,
    ProcessUserMessageInput,
)

class MessageHandler:
    """Handles Slack messages and interacts with an agent session."""
    def __init__(self, temporal_client: Client):
        self.temporal_client = temporal_client

    async def start(self):
        """Start the Slack bot."""
        slack_app = AsyncApp(token=settings.slack_bot_token)
        self._register_handlers(slack_app)

        handler = AsyncSocketModeHandler(slack_app, settings.slack_app_token)
        await handler.start_async()

    async def _set_thinking_status(self, set_status: SetStatus) -> None:
        """Set the status to indicate the bot is thinking."""
        await set_status("is thinking...")

    async def _signal_or_start_workflow(self, prompt: str, channel_id: str, thread_ts: str) -> str:
        """Start a new workflow or signal an existing workflow"""
        wf_id = "slack_session_" + thread_ts
        input = ProcessUserMessageInput(user_input=prompt, channel_id=channel_id, thread_ts=thread_ts)
        await self.temporal_client.start_workflow(
            ConversationWorkflow.run,
            settings.research_mode,
            id=wf_id,
            task_queue=settings.temporal_task_queue,
            start_signal=ConversationWorkflow.process_user_message.__name__,
            start_signal_args=[input],
        )
        return wf_id

    def _register_handlers(self, slack_app: AsyncApp) -> None:
        @slack_app.event("assistant_thread_context_changed")
        async def handle_assistant_thread_context_changed_events(body, logger):
            logger.info(body)

        @slack_app.event("assistant_thread_started")
        async def handle_assistant_thread_started_events(body, say: Say, set_suggested_prompts: SetSuggestedPrompts):
            title = "I'm your AI research assistant. I can analyze conversations, summarize discussions, and help you find insights from your Slack workspace. How can I help you?"
            prompts: List[Dict[str, str]] = [
                {
                    "title": "What are the most recent feature releases form Java SDK?",
                    "message": "What are the most recent feature releases form Java SDK?",
                },
                {
                    "title": "Ask about the latest Golang SDK release",
                    "message": "What's new in the latest Golang SDK release from last month? Can you provide details about new features and improvements?",
                },
            ]
            await set_suggested_prompts(title=title, prompts=prompts)

        """Register event handlers for the Slack app."""
        @slack_app.event("message")
        async def handle_dm(event: dict, say: Say, set_status: SetStatus, logger: logging.Logger):
            if event.get("channel_type") != "im" or event.get("subtype") or event.get("bot_id"):
                return

            text = (event.get("text") or "").strip()
            if not text:
                return

            await self._set_thinking_status(set_status)
            wf_id = await self._signal_or_start_workflow(text, channel_id = event["channel"], thread_ts = event["thread_ts"])
            
