from __future__ import annotations

from wtflow.infra.executables import Command, PyFunc


def f(): ...


def test_repr():
    assert repr(PyFunc(f)) == "PyFunc(target=tests.executables_test.f, args=(), kwargs={})"
    assert repr(Command("echo")) == "Command(cmd='echo')"
