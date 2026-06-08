import asyncio
import multiprocessing as mp
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.packages.configured_logger import get_logger
from app.packages.db.models import Task
from app.packages.db.session import SessionLocal
from app.packages.enums import TaskStatus
from app.services.worker.jobs import execute_job
from app.services.worker.process_registry import (
    get_process,
    process_semaphore,
    register_process,
    unregister_process,
)
from app.packages.configs import settings
logger = get_logger(__name__)


async def wait_process_with_cancel(task_uuid: UUID, process: mp.Process) -> str:
    while process.is_alive():
        await asyncio.sleep(settings.TIME_TO_EXECUTE_TASK)

        db: Session = SessionLocal()
        try:
            task = db.get(Task, task_uuid)
            if task and task.status == TaskStatus.CANCELLED:
                process.terminate()
                process.join()
                logger.info(f"Процесс остановлен {task.id}")
                return "cancelled"
        finally:
            db.close()

    process.join()
    return "completed" if process.exitcode == 0 else "failed"


async def process_task(task_id: str) -> None:
    task_uuid = UUID(task_id)

    async with process_semaphore:
        db: Session = SessionLocal()
        process: mp.Process | None = None

        try:
            task = db.get(Task, task_uuid)
            if not task:
                return

            if task.status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
                return

            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now(timezone.utc)
            db.add(task)
            db.commit()

            process = mp.Process(target=execute_job, args=(task_id,), daemon=False)
            process.start()

            await register_process(task_uuid, process)
            logger.info(f"Запущен процесс {task_id=}, {process.pid}")


            result = await wait_process_with_cancel(task_uuid, process)

            db.refresh(task)
            if task.status == TaskStatus.CANCELLED:
                logger.info(f"Задача {task.id} отмена до выполнения ")
                return

            if result == "completed":
                task.status = TaskStatus.COMPLETED
                task.result = f"Задача {task.id} выполнена!"
            else:
                task.status = TaskStatus.FAILED
                task.error = f"Задача {task.id} завершилась с ошибкой - {process.exitcode}"

            task.finished_at = datetime.now(timezone.utc)
            db.add(task)
            db.commit()

            logger.info("Finished task_id=%s status=%s", task_id, task.status)

        except Exception as exc:
            task = db.get(Task, task_uuid)
            if task:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                task.finished_at = datetime.now(timezone.utc)
                db.add(task)
                db.commit()

            if process is not None and process.is_alive():
                process.terminate()
                process.join()

            logger.exception("Failed task_id=%s", task_id)

        finally:
            await unregister_process(task_uuid)
            db.close()


async def cancel_running_task(task_id: str) -> bool:
    task_uuid = UUID(task_id)
    process = await get_process(task_uuid)

    if process is None:
        logger.info("Нет активных процессов в  task_id=%s", task_id)
        return False

    if process.is_alive():
        process.terminate()
        process.join()
        logger.info("Остановка процесса для задачи task_id=%s pid=%s", task_id, process.pid)

    await unregister_process(task_uuid)
    return True