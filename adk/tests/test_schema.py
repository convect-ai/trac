# test schema parsing and validation
from trac.schema.task import FILE_TYPE, AppDef, RunConfig, TaskDef


def test_task_spec_schema(task_spec):
    """
    Test task spec schema
    """

    task = TaskDef.parse_obj(task_spec)

    assert task.name == "task1"
    assert task.description == "task1 description"
    assert task.parameter.mount_path == "/parameters.json"
    assert task.parameter.parameters[0].name == "param1"
    assert task.parameter.parameters[0].type == "string"
    assert task.parameter.parameters[0].default == "default"
    assert task.parameter.parameters[0].description == "param1 description"
    assert task.parameter.parameters[1].name == "param2"
    assert task.parameter.parameters[1].type == "integer"
    assert task.parameter.parameters[1].default == 0
    assert task.parameter.parameters[1].description == "param2 description"
    assert task.io.files[0].name == "file1"
    assert task.io.files[0].type == FILE_TYPE.INPUT
    assert task.io.files[0].mount_path == "/mnt/file1"
    assert task.io.files[0].description == "file1 description"
    assert task.io.files[0].file_schema["type"] == "object"
    assert task.io.files[0].file_schema["properties"]["name"]["type"] == "string"
    assert task.io.files[0].file_schema["properties"]["age"]["type"] == "integer"
    assert task.io.files[1].name == "file2"
    assert task.io.files[1].type == FILE_TYPE.OUTPUT
    assert task.io.files[1].mount_path == "/mnt/file2"
    assert task.io.files[1].description == "file2 description"
    assert task.io.files[1].file_schema["type"] == "object"
    assert task.io.files[1].file_schema["properties"]["name"]["type"] == "string"
    assert task.io.files[1].file_schema["properties"]["age"]["type"] == "integer"
    assert task.container.image == "busybox"
    assert task.container.command == ["sh", "-c"]
    assert task.container.args == ["cat /mnt/file1 > /mnt/file2 && echo 'hello world'"]


def test_task_spec_parsing_with_handler(task_spec_using_handler):
    task = TaskDef.parse_obj(task_spec_using_handler)

    assert task.name == "task1"
    assert task.description == "task1 description"
    assert task.parameter.mount_path == "/parameters.json"
    assert task.parameter.parameters[0].name == "param1"
    assert task.parameter.parameters[0].type == "string"
    assert task.parameter.parameters[0].default == "default"
    assert task.parameter.parameters[0].description == "param1 description"
    assert task.parameter.parameters[1].name == "param2"
    assert task.parameter.parameters[1].type == "integer"
    assert task.parameter.parameters[1].default == 0
    assert task.parameter.parameters[1].description == "param2 description"
    assert task.io.files[0].name == "file1"
    assert task.io.files[0].type == FILE_TYPE.INPUT
    assert task.io.files[0].mount_path == "/mnt/file1"
    assert task.io.files[0].description == "file1 description"
    assert task.io.files[0].file_schema["type"] == "object"
    assert task.io.files[0].file_schema["properties"]["name"]["type"] == "string"
    assert task.io.files[0].file_schema["properties"]["age"]["type"] == "integer"
    assert task.io.files[1].name == "file2"
    assert task.io.files[1].type == FILE_TYPE.OUTPUT
    assert task.io.files[1].mount_path == "/mnt/file2"
    assert task.io.files[1].description == "file2 description"
    assert task.io.files[1].file_schema["type"] == "object"
    assert task.io.files[1].file_schema["properties"]["name"]["type"] == "string"
    assert task.io.files[1].file_schema["properties"]["age"]["type"] == "integer"

    assert task.handler.handler == "module1.handler1:handler1"


def test_app_spec_parsing(app_spec):
    app = AppDef.parse_obj(app_spec)

    assert app.name == "app1"
    assert app.description == "app1 description"
    assert app.tasks[0].name == "task1"
    assert len(app.tasks) == 1


def test_run_config_parsing(run_config):
    config = RunConfig.parse_obj(run_config)

    assert config.parameters["param1"] == "value1"
    assert config.parameters["param2"] == 1
    assert config.input_files["file1"]
