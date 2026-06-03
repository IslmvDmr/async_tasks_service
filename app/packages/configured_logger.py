import logging
import sys
from app.packages.configs import settings

def get_logger(name, level=logging.INFO):
    """
    Создает и возвращает сконфигурированный логгер.

    Args:
        name: имя логгера (обычно __name__)
        level: уровень логирования (по умолчанию INFO)

    Returns:
        logging.Logger: сконфигурированный логгер
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger


    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger