import asyncio

from slack.message_handler import MessageHandler
from temporal.client import connect as connect_temporal


async def run_bot():
    """Run Slack bot's message handler. Make sure you run the worker too."""

    client = await connect_temporal()
    await MessageHandler(client).start()

if __name__ == "__main__":
    asyncio.run(run_bot())
