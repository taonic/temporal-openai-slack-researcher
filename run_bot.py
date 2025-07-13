import asyncio

from slack.message_handler import MessageHandler
from slack.session_manager import SessionManager
from temporal.client import connect as connect_temporal


async def run_bot():
    """Run Slack bot's message handler. Make sure you run the worker too."""

    client = await connect_temporal()
    async with SessionManager(client=client) as manager:
        await MessageHandler(manager).start()

if __name__ == "__main__":
    asyncio.run(run_bot())
