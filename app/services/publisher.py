import aio_pika

from app.packages.configs import settings
from app.packages.enums import TaskPriority, TASK_PRIORITY_MAP



class TaskPublisher:
    def __init__(self, amqp_url: str):
        self.amqp_url = amqp_url

    async def publish_task(self, task_id: str, priority: TaskPriority) -> None:
        connection = await aio_pika.connect_robust(self.amqp_url)
        async with connection:
            channel = await connection.channel()

            await channel.declare_queue(
                settings.TASK_QUEUE_NAME,
                durable=True,
                arguments={"x-max-priority": settings.TASK_QUEUE_MAX_PRIORITY},
            )

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=task_id.encode(),
                    priority=TASK_PRIORITY_MAP[priority],
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=settings.TASK_QUEUE_NAME,
            )