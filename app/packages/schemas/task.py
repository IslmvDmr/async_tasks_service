from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.packages.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskRead(BaseModel):
    id: UUID
    title: str
    description: str | None
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    result: str | None
    error: str | None

    model_config = {"from_attributes": True}


class TaskStatusRead(BaseModel):
    id: UUID
    status: TaskStatus

    model_config = {"from_attributes": True}


class TaskListItem(BaseModel):
    id: UUID
    title: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TaskListItem]