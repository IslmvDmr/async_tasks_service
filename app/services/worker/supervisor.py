import asyncio

from app.packages.db.session import SessionLocal
from app.packages.repositories.task import TaskRepository
from app.services.worker.process_registry import has_process
from app.packages.configured_logger import get_logger
from app.services.worker.task_runner import cancel_running_task
logging = get_logger(__name__)

def get_old_tasks_sync():
    with SessionLocal() as db:
        repo = TaskRepository(db)
        return repo.get_old_tasks()

def cancel_task_in_db_sync(task_id):
    with SessionLocal() as db:
        repo = TaskRepository(db)
        task = repo.get(task_id)
        if task is None:
            return None
        return repo.cancel(task)

async def supervisor() -> None:
    """Супервизор следит за временем выполнения задач, раз в n-секунд проверяет старые задачи.
    Если задача работает больше отведенного времени - грохаем её."""
    while True:
        old_tasks = await asyncio.to_thread(get_old_tasks_sync,)
        for task in old_tasks:
            if await has_process(task.id):
                logging.info(f"Задача {task.id} работает слишком долго (запущена {task.started_at}), отменяем")

                await asyncio.to_thread(cancel_task_in_db_sync, task.id)
                stopped = await cancel_running_task(str(task.id))

                if stopped:
                    logging.info(f"Задача {task.id} успешно остановлена супервизором")
                else:
                    logging.warning(f"Процесс для задачи {task.id} не найден при остановке")

        await asyncio.sleep(10)