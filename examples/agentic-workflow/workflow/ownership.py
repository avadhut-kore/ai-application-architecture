"""Single-host execution ownership released by the OS on process death."""

from __future__ import annotations

import hashlib
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .errors import ConcurrentResumeConflictError


@contextmanager
def file_ownership(db_path: Path, workflow_id: str) -> Iterator[None]:
    directory = db_path.with_suffix(db_path.suffix + ".locks")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / hashlib.sha256(workflow_id.encode()).hexdigest()
    with path.open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ConcurrentResumeConflictError("Workflow is owned by a live process") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def memory_ownership(locks: dict[str, threading.Lock], workflow_id: str) -> Iterator[None]:
    lock = locks.setdefault(workflow_id, threading.Lock())
    if not lock.acquire(blocking=False):
        raise ConcurrentResumeConflictError("Workflow is owned by a live task")
    try:
        yield
    finally:
        lock.release()
