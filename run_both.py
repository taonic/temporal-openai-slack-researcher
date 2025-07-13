import asyncio

from temporal.worker import worker as temporal_worker
from slack.message_handler import MessageHandler

async def main():
    """A standalone runner than runs both the Temporal worker and Slack's message handler"""

    async with temporal_worker() as worker:
        await MessageHandler(worker.client).start()

if __name__ == "__main__":
    asyncio.run(main())
