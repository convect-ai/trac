import pytest
from trac_runtime.schema import AppSpec, TaskSpec


@pytest.fixture
def valid_task_spec():
    return {
        "name": "task1",
        "description": "task1 description",
        "parameters": [
            {
                "name": "param1",
                "type": "string",
                "default": "default",
                "description": "param1 description",
            },
            {
                "name": "param2",
                "type": "integer",
                "default": 0,
                "description": "param2 description",
            },
        ],
        "files": [
            {
                "name": "file1",
                "type": "input",
                "mount_path": "/mnt/file1",
                "description": "file1 description",
                "file_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                },
            },
            {
                "name": "file2",
                "type": "output",
                "mount_path": "/mnt/file2",
                "description": "file2 description",
                "file_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer"},
                    },
                },
            },
        ],
        "container": {
            "image": "image1",
            "tag": "tag1",
            "command": ["command1"],
            "args": ["arg1"],
            "envs": [["env1", "value1"]],
        },
    }


@pytest.fixture
def valid_app_spec(valid_task_spec):
    return {
        "name": "app1",
        "description": "app1 description",
        "tasks": [valid_task_spec],
    }


def test_task_spec_parsing(valid_task_spec):
    task_spec = TaskSpec.parse_obj(valid_task_spec)
    assert task_spec.name == "task1"
    assert task_spec.description == "task1 description"
    assert len(task_spec.parameters) == 2
    assert len(task_spec.files) == 2
    assert task_spec.container.image == "image1"
    assert task_spec.container.tag == "tag1"
    assert task_spec.container.command == ["command1"]
    assert task_spec.container.args == ["arg1"]
    assert task_spec.container.envs == [("env1", "value1")]


def test_app_spec_parsing(valid_app_spec):
    app_spec = AppSpec.parse_obj(valid_app_spec)
    assert app_spec.name == "app1"
    assert app_spec.description == "app1 description"
    assert len(app_spec.tasks) == 1
