from enum import StrEnum


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskStatus(StrEnum):
    NEW = "NEW"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


TASK_PRIORITY_MAP = {
    TaskPriority.LOW: 1,
    TaskPriority.MEDIUM: 5,
    TaskPriority.HIGH: 10,
}