import json
import os

import click

from ..builder.build import build_app_image
from ..runtime.run import get_logs, get_output, get_status, get_task_spec
from ..runtime.run import submit as submit_task
from ..schema.task import RunConfig


@click.group()
def cli():
    pass


@cli.group()
def task():
    pass


@task.command()
@click.option(
    "--app-name", required=True, help="name of the app, also the name of the image"
)
@click.option("--tag", required=False, default="latest", help="Image tag")
@click.option("--task-name", "--n", required=True, help="Task name")
@click.option("--backend", required=False, default="docker", help="Backend to use")
@click.option(
    "--backend-config",
    required=False,
    multiple=True,
    help="Backend config in the form of key=value",
)
@click.option(
    "--input-json",
    required=False,
    help="Input json file, with key as the input name and value as the path to the file",
)
@click.option(
    "--parameter-json",
    required=False,
    help="Parameter json file, with key as the parameter name and value as the value",
)
def submit(
    app_name, tag, task_name, backend, backend_config, input_json, parameter_json
):
    """
    Submit a task
    """
    # create a dict for backend config
    backend_config_dict = {}
    for config in backend_config:
        key, value = config.split("=")
        backend_config_dict[key] = value

    # create a dict for input files
    input_files = {}
    if input_json:
        with open(input_json) as f:
            input_files = json.load(f)

    # for each value in the input_files dict, verify if the file exists
    for input_file in input_files:
        if not os.path.exists(input_files[input_file]):
            raise Exception(f"Input file {input_files[input_file]} not found")

    # create a dict for parameters
    parameters = {}
    if parameter_json:
        with open(parameter_json) as f:
            parameters = json.load(f)

    # create a run config
    run_config = RunConfig(
        parameters=parameters,
        input_files=input_files,
    )

    # get the task spec
    task_spec = get_task_spec(app_name, tag, task_name)

    # if tag is specified, override the tag in the task spec
    if tag:
        task_spec.container.tag = tag

    # submit the task
    job_handle = submit_task(
        task_spec=task_spec,
        run_config=run_config,
        backend=backend,
        backend_config=backend_config_dict,
    )

    print(f"Job submitted with handle {job_handle}")


@task.command()
@click.argument("job_handle")
@click.option(
    "--app-name", required=False, help="name of the app, also the name of the image"
)
@click.option("--backend", required=False, default="docker", help="Backend to use")
@click.option(
    "--backend-config",
    required=False,
    multiple=True,
    help="Backend config in the form of key=value",
)
def status(job_handle, backend, backend_config):
    """
    Get the status of a task
    """
    # create a dict for backend config
    backend_config_dict = {}
    for config in backend_config:
        key, value = config.split("=")
        backend_config_dict[key] = value

    # get the status
    status = get_status(job_handle, backend, backend_config_dict)

    print(f"Status: {status}")


@task.command()
@click.argument("job_handle")
@click.option(
    "--app-name", required=True, help="name of the app, also the name of the image"
)
@click.option("--tag", required=False, default="latest", help="Image tag")
@click.option("--task-name", "--n", required=True, help="Task name")
@click.option("--backend", required=False, default="docker", help="Backend to use")
@click.option(
    "--backend-config",
    required=False,
    multiple=True,
    help="Backend config in the form of key=value",
)
def output(job_handle, app_name, tag, task_name, backend, backend_config):
    """
    Get the output of a task
    """
    # create a dict for backend config
    backend_config_dict = {}
    for config in backend_config:
        key, value = config.split("=")
        backend_config_dict[key] = value

    task_spec = get_task_spec(app_name, tag, task_name)

    # get the output
    output = get_output(job_handle, task_spec, backend, backend_config_dict)
    print(f"Output: {output}")


@task.command
@click.argument("job_handle")
@click.option("--backend", required=False, default="docker", help="Backend to use")
@click.option(
    "--backend-config",
    required=False,
    multiple=True,
    help="Backend config in the form of key=value",
)
def logs(job_handle, backend, backend_config):
    """
    Get the logs of a task
    """
    # create a dict for backend config
    backend_config_dict = {}
    for config in backend_config:
        key, value = config.split("=")
        backend_config_dict[key] = value

    # get the logs
    logs = get_logs(job_handle, backend, backend_config_dict)

    print(f"Logs: {logs}")


@cli.command()
@click.argument(
    "folder",
    type=click.Path(exists=True),
)
@click.option("--image-name", help="The name of the image to build")
@click.option("--clear-cache", is_flag=True, help="Clear the cache before building")
def build(folder, image_name, clear_cache):
    build_app_image(folder, image_name, clear_cache)


def main():
    cli()


if __name__ == "__main__":
    main()
