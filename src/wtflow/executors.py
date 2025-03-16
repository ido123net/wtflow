from __future__ import annotations

import logging
import multiprocessing
import subprocess
import sys
import traceback
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wtflow.executables import Command, Executable, PyFunc
    from wtflow.nodes import Node

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


class Executor(ABC):
    """Base class for execution logic."""

    def __init__(self, executable: Executable) -> None:
        self._executable = executable
        self._returncode: int | None = None

    @abstractmethod
    def _execute(self) -> None:
        """Execute logic, should be overridden by subclasses."""

    @abstractmethod
    def _wait(self) -> None:
        """Wait for process completion."""

    @property
    def node(self) -> Node:
        return self._executable.node

    def execute(self) -> None:
        self._execute()
        self._wait()


class MultiprocessingExecutor(Executor):
    """Runs a Python function asynchronously in a separate process using os.pipe."""

    @property
    def executable(self) -> PyFunc:
        if TYPE_CHECKING:
            assert isinstance(self._executable, PyFunc)
        return self._executable

    def _execute(self) -> None:
        def _target() -> None:
            sys.stdout = self.node.stdout_artifact.path.open("w")
            sys.stderr = self.node.stderr_artifact.path.open("w")
            try:
                self.executable.func(*self.executable.args, **self.executable.kwargs)
            except Exception:
                traceback.print_exc()
                raise

        self._process = multiprocessing.Process(target=_target)
        self._process.start()

    def _wait(self) -> None:
        self._process.join(self.executable.timeout)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join()
        self._returncode = self._process.exitcode


class SubprocessExecutor(Executor):
    """Runs an external command asynchronously using subprocess."""

    @property
    def executable(self) -> Command:
        if TYPE_CHECKING:
            assert isinstance(self._executable, Command)
        return self._executable

    def _execute(self) -> None:
        self._process = subprocess.Popen(
            self.executable.cmd,
            shell=True,
            stdout=self.node.stdout_artifact.path.open("wb"),
            stderr=self.node.stderr_artifact.path.open("wb"),
        )

    def _wait(self) -> None:
        try:
            self._returncode = self._process.wait(self.executable.timeout)
        except subprocess.TimeoutExpired:
            self._process.terminate()
            self._returncode = self._process.wait()
