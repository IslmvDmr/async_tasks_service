import asyncio
import multiprocessing as mp

import aio_pika

from app.packages.configs import settings
from app.services.worker.supervisor import supervisor
from app.services.worker.task_runner import process_task
from app.packages.configured_logger import get_logger
logger = get_logger(__name__)

async def consume_queue() -> None:
    connection = await aio_pika.connect_robust(settings.AMQP_URL)
    channel = await connection.channel()
    logger.info("Сервис по обработке сообщений запущен...")
    await channel.set_qos(prefetch_count=10)

    queue = await channel.declare_queue(
        settings.TASK_QUEUE_NAME,
        durable=True,
        arguments={"x-max-priority": settings.TASK_QUEUE_MAX_PRIORITY},
    )

    background_tasks: set[asyncio.Task] = set()

    async with queue.iterator() as iterator:
        async for message in iterator:
            task_id = message.body.decode()

            async def runner(msg=message, current_task_id=task_id):
                async with msg.process():
                    await process_task(current_task_id)

            task = asyncio.create_task(runner())
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)


async def main() -> None:
    await asyncio.gather(
        supervisor(),
        consume_queue(),
    )


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    asyncio.run(main())