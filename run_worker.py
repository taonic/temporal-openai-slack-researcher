import asyncio
import logging

from temporal.worker import worker as temporal_worker

async def worker_main():
    """Runs Temporal worker"""

    logging.basicConfig(level=logging.INFO)
    interrupt_event = asyncio.Event()
    
    async with temporal_worker():
        # Wait until interrupted
        logging.info("Worker started, ctrl+c to exit")
        await interrupt_event.wait()

if __name__ == "__main__":
    asyncio.run(worker_main())
