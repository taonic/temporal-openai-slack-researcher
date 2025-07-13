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

    async def _poll_thoughts_to_slack(self, session: Session, say: Say, set_status: SetStatus) -> None:
        """Poll thoughts from the agent session and send them to Slack."""
        try:
            while True:
                thoughts = await session.thoughts()
                if thoughts:
                    for line in thoughts:
                        await say((f"🧠 {slackStyle.convert(line)}"))
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    def _register_handlers(self, slack_app: AsyncApp) -> None:
        """Register event handlers for the Slack app."""
        @slack_app.event("message")
        async def handle_dm(event: dict, say: Say, set_status: SetStatus, logger: logging.Logger):
            await self._set_thinking_status(set_status)
            
            if event.get("channel_type") != "im":
                return
            if event.get("subtype") or event.get("bot_id"):
                return

            slack_session_id = event["thread_ts"]
            session = await self.session_manager.get_session(slack_session_id)

            text = (event.get("text") or "").strip()
            if not text:
                return

            poll = asyncio.create_task(self._poll_thoughts_to_slack(session, say, set_status))
            try:
                await self._set_thinking_status(set_status)
                reply = await session.prompt(text) # This will block until the agent/workflow responds
                await say(slackStyle.convert(reply))
            finally:
                poll.cancel()

        @slack_app.event("assistant_thread_context_changed")
        async def handle_assistant_thread_context_changed_events(body, logger):
            logger.info(body)

        @slack_app.event("assistant_thread_started")
        async def handle_assistant_thread_started_events(body, say: Say, set_suggested_prompts: SetSuggestedPrompts):
            title = "I'm your AI research assistant. I can analyze conversations, summarize discussions, and help you find insights from your Slack workspace. How can I help you?"
            prompts: List[Dict[str, str]] = [
                {
                    "title": "Show me the latest blogs on Agentic SDK from last month",
                    "message": "Show me the latest blogs on Agentic SDK from last month",
                },
                {
                    "title": "Ask about the latest Golang SDK release",
                    "message": "What's new in the latest Golang SDK release from last month? Can you provide details about new features and improvements?",
                },
            ]
            await set_suggested_prompts(title=title, prompts=prompts)
