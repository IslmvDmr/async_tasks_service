import os
import time

from app.packages.configured_logger import get_logger

logger = get_logger(__name__)


def execute_job(task_id: str) -> None:
    '''Имитация фоновой задачи'''
    pid = os.getpid()
    logger.info(f"Задача запущена {task_id=} {pid=}")
    for i in range(10):
        time.sleep(1)
        logger.info(f"Задача {task_id} Выполняю сложный расчет, обучаю модели, загружаю данные. {i} ")
    logger.info(f"Задача завершена {task_id=} {pid=}")
