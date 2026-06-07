from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.packages.configs import settings
from app.packages.enums import TaskStatus
from app.packages.repositories.task import TaskRepository
from app.packages.schemas.task import TaskCreate
from app.services.publisher import TaskPublisher
from app.packages.configured_logger import get_logger

logging = get_logger(__name__)

class TaskService:
    """
       Сервис для работы с задачами.

       Собирает вместе репозиторий и публикацию в очередь.
       Содержит всю бизнес-логику по задачам.

       """
    def __init__(self, db: Session):
        self.repo = TaskRepository(db)
        self.publisher = TaskPublisher(settings.AMQP_URL)

    async def create_task(self, data: TaskCreate):
        task = self.repo.create(data)
        task.status = TaskStatus.PENDING
        self.repo.save()
        await self.publisher.publish_task(str(task.id), task.priority)
        logging.info(f"Создана задача: {str(task.id)} ")
        return task

    def get_task(self, task_id: UUID):
        task = self.repo.get(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        logging.info(f"Запрос статуса задачи: {str(task.id)} ")
        return task

    def list_tasks(self, *, status_filter: TaskStatus | None, limit: int, offset: int):
        return self.repo.list(status=status_filter, limit=limit, offset=offset)

    def cancel_task(self, task_id: UUID):
        task = self.get_task(task_id)
        logging.info(f"Отмена задачи: {str(task.id)} ")
        return self.repo.cancel(task)