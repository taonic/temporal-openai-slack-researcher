import asyncio

from temporal.worker import worker as temporal_worker
from slack.message_handler import MessageHandler
from slack.session_manager import SessionManager

async def main():
    async with temporal_worker() as worker:
        async with SessionManager(client=worker.client) as manager:
            await MessageHandler(manager).start()

if __name__ == "__main__":
    asyncio.run(main())
