import asyncio
import logging
from typing import List, Dict

from slack_bolt.async_app import AsyncApp
from slack_bolt import SetStatus, Say, SetSuggestedPrompts
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slackstyler import SlackStyler

from config import settings
from .session_manager import SessionManager
from .session import Session

slackStyle = SlackStyler()

class MessageHandler:
    """Handles Slack messages and interacts with an agent session."""
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.bot_token: str = settings.slack_bot_token
        self.app_token: str = settings.slack_app_token

    async def start(self):
        """Start the Slack bot."""
        slack_app = AsyncApp(token=self.bot_token)
        self._register_handlers(slack_app)

        handler = AsyncSocketModeHandler(slack_app, self.app_token)
        await handler.start_async()


    async def _set_thinking_status(self, set_status: SetStatus) -> None:
        """Set the status to indicate the bot is thinking."""
        await set_status("is thinking...")

    def _register_handlers(self, slack_app: AsyncApp) -> None:
        @slack_app.event("assistant_thread_context_changed")
        async def handle_assistant_thread_context_changed_events(body, logger):
            logger.info(body)

        @slack_app.event("assistant_thread_started")
        async def handle_assistant_thread_started_events(body, say: Say, set_suggested_prompts: SetSuggestedPrompts):
            title = "I'm your AI research assistant. I can analyze conversations, summarize discussions, and help you find insights from your Slack workspace. How can I help you?"
            prompts: List[Dict[str, str]] = [
                {
                    "title": "Show me the latest blog posts from Temporal on Agentic AI from last month",
                    "message": "Show me the latest blog posts from Temporal on Agentic AI from last month",
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
            await self._set_thinking_status(set_status)
            
            if event.get("channel_type") != "im" or event.get("subtype") or event.get("bot_id"):
                return

            thread_ts = event["thread_ts"]
            channel_id = event["channel"]

            text = (event.get("text") or "").strip()
            if not text:
                return
            
            session = await self.session_manager.get_session(thread_ts)
            # This will block until the agent/workflow responds
            await session.prompt(prompt=text, thread_ts=thread_ts, channel_id=channel_id)
