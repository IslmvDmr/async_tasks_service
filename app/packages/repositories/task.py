from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.packages.db.models import Task
from app.packages.enums import TaskStatus
from app.packages.schemas.task import TaskCreate
from app.packages.configs import settings

class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: TaskCreate) -> Task:
        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            status=TaskStatus.NEW,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def get(self, task_id: UUID) -> Task | None:
        return self.db.get(Task, task_id)

    def list(self, *, status: TaskStatus | None, limit: int, offset: int) -> tuple[int, list[Task]]:
        count_stmt = select(func.count()).select_from(Task)
        items_stmt = select(Task).order_by(Task.created_at.desc()).limit(limit).offset(offset)

        if status:
            count_stmt = count_stmt.where(Task.status == status)
            items_stmt = items_stmt.where(Task.status == status)

        total = self.db.scalar(count_stmt) or 0
        items = list(self.db.scalars(items_stmt).all())
        return total, items

    def save(self) -> None:
        self.db.commit()

    def cancel(self, task: Task) -> Task:
        if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
            return task
        task.status = TaskStatus.CANCELLED
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_old_tasks(self, *, seconds: int = settings.TIME_TO_WAIT_TASK):
        """Возвращает задачи, которые были созданы более указанного количества минут назад.
           Не буду выносить логику отдельно, нужен для работы супервизора, который будет убивать задачи.
        Args:
            seconds: количество минут (по умолчанию 10)

        """
        from datetime import datetime, timedelta

        threshold_time = datetime.now() - timedelta(seconds=seconds)

        stmt = select(Task).where(Task.created_at < threshold_time)
        items = list(self.db.scalars(stmt).all())
        return items

