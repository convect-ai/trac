import pytest


@pytest.fixture
def task_spec():
    """
    A task spec simply cat all the input file contents
    write a hello world to the output file using image busybox
    """

    spec = {
        "name": "task1",
        "description": "task1 description",
        "parameter": {
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
        "io": {
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
        "container": {
            "image": "busybox",
            "tag": "latest",
            "command": ["sh", "-c"],
            "args": ["cat /mnt/file1 > /mnt/file2 && echo 'hello world'"],
            "envs": [],
        },
    }

    return spec


@pytest.fixture
def task_spec_using_handler():
    """
    A task spec using handler definition instead of container def
    """

    spec = {
        "name": "task1",
        "description": "task1 description",
        "parameter": {
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
        "io": {
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
        "handler": {
            "handler": "module1.handler1:handler1",
        },
    }

    return spec


@pytest.fixture
def task_spec_will_fail(task_spec):
    """
    A task spec that will fail
    """

    task_spec["container"]["args"] = ["echo 'this will failed' && exit 1"]
    return task_spec


@pytest.fixture
def run_config(tmp_path):
    """
    A concrete run config
    """
    input_file1 = tmp_path / "input1"
    input_file1.write_text("hello world")

    config = {
        "parameters": {"param1": "value1", "param2": 1},
        "input_files": {"file1": str(input_file1)},
    }

    return config


@pytest.fixture
def app_spec(task_spec):
    """
    An app spec with a single task
    """

    spec = {
        "name": "app1",
        "description": "app1 description",
        "tasks": [task_spec],
    }

    return spec
