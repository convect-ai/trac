# the entry point to trigger the runtime

import json
from typing import Dict, Optional

import docker

from ..schema.task import AppDef, RunConfig, TaskDef
from .base import JOB_STATUS, BaseExecutor
from .docker import LocalDockerExecutor
from .k8s import K8sExecutor

BACKENDS = {
    "docker": LocalDockerExecutor,
    "k8s": K8sExecutor,
}


def get_task_spec(image, tag, task_name) -> TaskDef:
    """
    Get the task spec for the given image
    """
    # create a docker client
    client = docker.from_env()

    # verify if the image tag exists, if not, try to pull it. If it fails, throw an error
    try:
        client.images.get(image + ":" + tag)
    except docker.errors.ImageNotFound:
        try:
            client.images.pull(image, tag=tag)
        except docker.errors.ImageNotFound:
            raise Exception(f"Image {image}:{tag} not found")

    # docker run --rm image:tag -- spec
    result = client.containers.run(
        image=image + ":" + tag,
        command="-- spec",
        detach=False,
        remove=True,
    )

    # parse the result to get the task spec
    try:
        app_spec = json.loads(result)
        app_spec = AppDef.parse_obj(app_spec)
    except:
        print("Error parsing the app spec")
        print(result)
        raise Exception("Error parsing the app spec")

    # create a task spec
    # get the task spec from the app spec
    task_spec = None
    for task in app_spec.tasks:
        task_name_slug = task.name.replace(" ", "-")
        if task_name_slug == task_name or task.name == task_name:
            task_spec = task
            break

    if not task_spec:
        raise Exception(f"Task {task_name} not found in the app spec")

    return task_spec


def create_executor(
    task_spec: TaskDef,
    run_config: RunConfig,
    backend: str = "docker",
    backend_config: Optional[Dict] = None,
) -> BaseExecutor:
    """
    Create an executor for the given backend
    """
    if backend not in BACKENDS:
        raise Exception(f"Backend {backend} not supported")

    backend_config = backend_config or {}

    if not task_spec or not run_config:
        # skip the validation
        return BACKENDS[backend](
            task_spec, run_config, skip_validation=True, **backend_config
        )

    return BACKENDS[backend](task_spec, run_config, **backend_config)


def submit(
    task_spec: TaskDef,
    run_config: RunConfig,
    backend: str = "docker",
    backend_config: Optional[Dict] = None,
) -> str:
    """
    Submit a task to the given backend
    """
    executor = create_executor(task_spec, run_config, backend, backend_config)

    job_handle = executor.submit()
    return job_handle


def get_status(
    job_handle: str, backend: str = "docker", backend_config: Optional[Dict] = None
) -> JOB_STATUS:
    """
    Get the status of a task
    """
    backend_config = backend_config or {}
    executor = create_executor(None, None, backend, backend_config)

    status = executor.get_status(job_handle=job_handle)
    return status


def get_output(
    job_handle: str,
    task_spec: TaskDef,
    backend: str = "docker",
    backend_config: Optional[Dict] = None,
) -> Dict[str, bytes]:
    """
    Get the output of a task
    """
    executor = create_executor(task_spec, None, backend, backend_config)

    output = executor.get_output(job_handle)
    return output


def get_logs(
    job_handle: str, backend: str = "docker", backend_config: Optional[Dict] = None
) -> str:
    """
    Get the logs of a task
    """
    executor = create_executor(None, None, backend, backend_config)

    logs = executor.get_logs(job_handle)
    return logs
