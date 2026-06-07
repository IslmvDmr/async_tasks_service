import asyncio
import multiprocessing as mp
from uuid import UUID
from app.packages.configs import settings

MAX_CONCURRENT_PROCESSES = settings.MAX_CONCURRENT_PROCESSES

active_processes = {}
active_processes_lock = asyncio.Lock()
process_semaphore = asyncio.Semaphore(MAX_CONCURRENT_PROCESSES)


async def register_process(task_uuid: UUID, process: mp.Process) -> None:
    async with active_processes_lock:
        active_processes[task_uuid] = process


async def unregister_process(task_uuid: UUID) -> None:
    async with active_processes_lock:
        active_processes.pop(task_uuid, None)


async def get_process(task_uuid: UUID) -> mp.Process | None:
    async with active_processes_lock:
        return active_processes.get(task_uuid)


async def has_process(task_uuid: UUID) -> bool:
    async with active_processes_lock:
        return task_uuid in active_processes


async def active_processes_count() -> int:
    async with active_processes_lock:
        return len(active_processes)