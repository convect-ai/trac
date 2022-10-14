import pytest

from ..schema import FILE_TYPE, AppDef, RunConfig, TaskDef


@pytest.fixture
def task_spec():
    """
    A task spec simply cat all the input file contents
    write a hello world to the output file
    using image busybox
    """

    spec = {
        "name": "task1",
        "description": "task1 description",
        "parameters": {
            "mount_path": "/parameters.json",
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
        },
        "files": {
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
            ]
        },
        # cat all the input file contents and write a hello world to the output file
        "container": {
            "image": "busybox",
            "tag": "latest",
            "command": [
                "sh",
                "-c",
            ],
            "args": [
                "cat /mnt/file1 > /mnt/file2; echo 'hello world' >> /mnt/file2; echo 'hello world'",
            ],
            "envs": [["env1", "value1"]],
        },
    }

    return TaskDef.parse_obj(spec)


@pytest.fixture
def failed_task_spec(task_spec):
    """
    A task spec where the container always return a non-zero exit code (failed)
    """
    task_spec.container.args = ["echo 'failed job'; exit 1"]
    return task_spec


@pytest.fixture
def run_config(tmp_path):
    # create two temp input files
    input_file1 = tmp_path / "input1"
    input_file1.write_text("hello world")

    config = {
        "parameters": {"param1": "value1", "param2": 1},
        "input_files": {"file1": str(input_file1)},
    }

    return RunConfig.parse_obj(config)
