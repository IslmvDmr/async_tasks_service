from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.packages.db.dependencies import get_db
from app.packages.enums import TaskStatus
from app.packages.schemas.task import TaskCreate, TaskListResponse, TaskRead, TaskStatusRead
from app.services.task_service import TaskService
from app.packages.configured_logger import get_logger

logging = get_logger(__name__)
router = APIRouter(prefix="/api/routers/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    service = TaskService(db)

    return await service.create_task(payload)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    status: TaskStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = TaskService(db)
    total, items = service.list_tasks(status_filter=status, limit=limit, offset=offset)
    return TaskListResponse(total=total, limit=limit, offset=offset, items=items)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.get_task(task_id)


@router.delete("/{task_id}", response_model=TaskRead)
def cancel_task(task_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(db)
    return service.cancel_task(task_id)


@router.get("/{task_id}/status", response_model=TaskStatusRead)
def get_task_status(task_id: UUID, db: Session = Depends(get_db)):
    service = TaskService(db)
    task = service.get_task(task_id)
    return TaskStatusRead.model_validate(task)


