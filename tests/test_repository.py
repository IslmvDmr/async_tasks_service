import uuid
from datetime import datetime, timezone, timedelta
import pytest
from app.packages.db.models import Task
from app.packages.enums import TaskPriority, TaskStatus
from app.packages.repositories.task import TaskRepository
from app.packages.schemas.task import TaskCreate


class TestTaskRepository:
    def test_create_task(self, db):
        repo = TaskRepository(db)
        data = TaskCreate(title="My Task", description="desc", priority=TaskPriority.HIGH)
        task = repo.create(data)
        repo.save()
        assert task.id is not None
        assert task.title == "My Task"
        assert task.status == TaskStatus.NEW

    def test_create_task_default_priority(self, db):
        repo = TaskRepository(db)
        data = TaskCreate(title="Simple Task")
        task = repo.create(data)
        repo.save()
        assert task.priority == TaskPriority.MEDIUM

    def test_get_existing_task(self, db, sample_task):
        repo = TaskRepository(db)
        result = repo.get(sample_task.id)
        assert result is not None
        assert result.id == sample_task.id

    def test_get_nonexistent_task(self, db):
        repo = TaskRepository(db)
        assert repo.get(uuid.uuid4()) is None

    def test_list_tasks_no_filter(self, db):
        repo = TaskRepository(db)
        for i in range(3):
            t = Task(title=f"Task {i}", priority=TaskPriority.LOW, status=TaskStatus.NEW,
                     created_at=datetime.now(timezone.utc))
            db.add(t)
        db.commit()
        total, items = repo.list(status=None, limit=10, offset=0)
        assert total == 3
        assert len(items) == 3

    def test_list_tasks_with_status_filter(self, db):
        repo = TaskRepository(db)
        for status in [TaskStatus.NEW, TaskStatus.PENDING, TaskStatus.PENDING]:
            t = Task(title="Task", priority=TaskPriority.LOW, status=status,
                     created_at=datetime.now(timezone.utc))
            db.add(t)
        db.commit()
        total, items = repo.list(status=TaskStatus.PENDING, limit=10, offset=0)
        assert total == 2
        assert all(t.status == TaskStatus.PENDING for t in items)

    def test_list_tasks_pagination(self, db):
        repo = TaskRepository(db)
        for i in range(5):
            t = Task(title=f"Task {i}", priority=TaskPriority.LOW, status=TaskStatus.NEW,
                     created_at=datetime.now(timezone.utc))
            db.add(t)
        db.commit()
        total, items = repo.list(status=None, limit=2, offset=0)
        assert total == 5
        assert len(items) == 2

    def test_cancel_new_task(self, db, sample_task):
        repo = TaskRepository(db)
        result = repo.cancel(sample_task)
        assert result.status == TaskStatus.CANCELLED

    @pytest.mark.parametrize("status", [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED])
    def test_cancel_terminal_statuses_unchanged(self, db, status):
        repo = TaskRepository(db)
        task = Task(title="Terminal", priority=TaskPriority.LOW, status=status,
                    created_at=datetime.now(timezone.utc))
        db.add(task)
        db.commit()
        result = repo.cancel(task)
        assert result.status == status

