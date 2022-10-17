import pytest
from trac_runtime.schema import AppDef, TaskDef


@pytest.fixture
def valid_app_spec(task_spec):
    return {
        "name": "app1",
        "description": "app1 description",
        "tasks": [task_spec],
    }


def test_task_spec_parsing(task_spec):
    task_spec = TaskDef.parse_obj(task_spec)
    assert task_spec.name == "task1"
    assert task_spec.description == "task1 description"
    assert len(task_spec.parameters.parameters) == 2
    assert len(task_spec.files.files) == 2
    assert task_spec.container.image == "busybox"
    assert task_spec.container.tag == "latest"
    assert task_spec.container.command == ["sh", "-c"]
    assert task_spec.container.args == [
        "cat /mnt/file1 > /mnt/file2; echo 'hello world' >> /mnt/file2; echo 'hello world'"
    ]
    assert task_spec.container.envs == [("env1", "value1")]


def test_app_spec_parsing(valid_app_spec):
    app_spec = AppDef.parse_obj(valid_app_spec)
    assert app_spec.name == "app1"
    assert app_spec.description == "app1 description"
    assert len(app_spec.tasks) == 1
