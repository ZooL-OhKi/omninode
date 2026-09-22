import pytest

from mqtt_service import TaskRemoteError, TaskTimeoutError


def test_error_types_are_available():
    assert issubclass(TaskTimeoutError, Exception)
    assert issubclass(TaskRemoteError, Exception)
