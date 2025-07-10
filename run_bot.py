import asyncio

from slack.message_handler import MessageHandler
from slack.session_manager import SessionManager


async def run_bot():
    """Run the Slack bot with the agent."""

    async with SessionManager(app_name="slack_bot") as manager:
        await MessageHandler(manager).start()

if __name__ == "__main__":
    asyncio.run(run_bot())
