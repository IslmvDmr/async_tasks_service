import uuid
from unittest.mock import AsyncMock, patch
import pytest
from app.packages.enums import TaskPriority, TaskStatus
from app.packages.schemas.task import TaskCreate
from app.services.task_service import TaskService


class TestTaskService:
    @pytest.mark.asyncio
    async def test_create_task_success(self, db, mock_publisher):
        service = TaskService(db)
        data = TaskCreate(title="New Task", priority=TaskPriority.HIGH)
        task = await service.create_task(data)
        assert task.title == "New Task"
        assert task.status == TaskStatus.PENDING
        mock_publisher.publish_task.assert_awaited_once_with(str(task.id), task.priority)

    @pytest.mark.asyncio
    async def test_create_task_publishes_correct_priority(self, db, mock_publisher):
        service = TaskService(db)
        data = TaskCreate(title="Priority Task", priority=TaskPriority.LOW)
        task = await service.create_task(data)
        mock_publisher.publish_task.assert_awaited_once_with(str(task.id), TaskPriority.LOW)

    def test_get_task_found(self, db, sample_task):
        service = TaskService(db)
        result = service.get_task(sample_task.id)
        assert result.id == sample_task.id

    def test_get_task_not_found_raises_404(self, db):
        from fastapi import HTTPException
        service = TaskService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.get_task(uuid.uuid4())
        assert exc_info.value.status_code == 404
        assert "Task not found" in exc_info.value.detail

    def test_list_tasks(self, db, sample_task):
        service = TaskService(db)
        total, items = service.list_tasks(status_filter=None, limit=10, offset=0)
        assert total >= 1

    def test_list_tasks_with_status_filter(self, db, sample_task):
        service = TaskService(db)
        total, items = service.list_tasks(status_filter=TaskStatus.NEW, limit=10, offset=0)
        assert all(t.status == TaskStatus.NEW for t in items)

    def test_cancel_task_success(self, db, sample_task):
        service = TaskService(db)
        result = service.cancel_task(sample_task.id)
        assert result.status == TaskStatus.CANCELLED

    def test_cancel_task_not_found(self, db):
        from fastapi import HTTPException
        service = TaskService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.cancel_task(uuid.uuid4())
        assert exc_info.value.status_code == 404
