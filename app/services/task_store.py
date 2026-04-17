from __future__ import annotations

from threading import Lock
from typing import Dict, Optional


class InMemoryTaskStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, dict] = {}
        self._lock = Lock()

    def create_task(self, task: dict) -> dict:
        with self._lock:
            self._tasks[task["id"]] = task
            return self._tasks[task["id"]]

    def get_task(self, task_id: str) -> Optional[dict]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, updates: dict) -> Optional[dict]:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task.update(updates)
            return task

    def all_tasks(self) -> Dict[str, dict]:
        with self._lock:
            return dict(self._tasks)


task_store = InMemoryTaskStore()