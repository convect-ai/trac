import io
import json
import logging
import tarfile
import tempfile

import docker

from ..schema.task import FILE_TYPE, RunConfig, TaskDef
from .base import JOB_STATUS, BaseExecutor

LOG = logging.getLogger(__name__)


class LocalDockerExecutor(BaseExecutor):
    """
    Executor for running tasks locally using docker
    """

    def __init__(self, task_def: TaskDef, run_config: RunConfig):
        super().__init__(task_def, run_config)
        self.docker_client = docker.from_env()

    def compile(self):
        """
        For the compile step, we do nothing but return the task_spec
        """
        return self.task_spec

    def submit(self):
        """
        For submit step, we create a docker container as specified by task_spec on the background
        and return its id as job handle
        """
        client = self.docker_client
        self.compiled_task = self.compile()
        compiled_task = self.compiled_task

        entrypoint = compiled_task.container.command
        command = compiled_task.container.args
        image = compiled_task.container.image
        tag = compiled_task.container.tag
        envs = compiled_task.container.envs
        envs = [f"{env[0]}={env[1]}" for env in envs]

        vols = self.preprocess()

        # create a container on the background
        container = client.containers.run(
            image=image + ":" + tag,
            entrypoint=entrypoint,
            command=command,
            detach=True,
            volumes=vols,
            environment=envs,
        )

        return container.id

    def preprocess(self):
        """
        For preprocess step, we save all the parameter as a temp json file that won't be deleted
        Create a docker mount point for each input file and the json file
        """
        run_config = self.run_config
        task_spec = self.task_spec
        parameters = run_config.parameters
        parameter_file = tempfile.NamedTemporaryFile(delete=False)
        parameter_file.write(json.dumps(parameters).encode())
        parameter_file.close()

        parameter_mount_point = self.task_spec.parameter.mount_path
        vols = {
            parameter_file.name: {
                "bind": parameter_mount_point,
                "mode": "ro",
            }
        }

        for file in run_config.input_files:

            # search under task_spec['files'] for the file
            mount_path = None
            for file_spec in task_spec.io.files:
                if file_spec.name == file:
                    mount_path = file_spec.mount_path
                    break
            else:
                raise Exception(f"Input file {file} not found in task_spec")

            vols[run_config.input_files[file]] = {
                "bind": mount_path,
                "mode": "ro",
            }

        return vols

    def get_status(self, job_handle):
        """
        Given a container id, return its status
        """
        client = self.docker_client
        container = client.containers.get(job_handle)
        status = container.status

        # map docker status to job status
        if status == "created":
            return JOB_STATUS.PENDING
        elif status == "running":
            return JOB_STATUS.RUNNING
        elif status == "exited":
            # check the exit code
            exit_code = container.attrs["State"]["ExitCode"]
            if exit_code == 0:
                return JOB_STATUS.SUCCESS
            else:
                return JOB_STATUS.FAILED
        else:
            return JOB_STATUS.FAILED

    def get_output(self, job_handle):
        """
        Given a container id, return the output files as a dictionary
        """
        client = self.docker_client
        container = client.containers.get(job_handle)
        # make sure the container is finished
        if container.status != "exited":
            raise Exception("Container not finished yet")

        output_files = {}

        for file in self.task_spec.io.files:
            if file.type == FILE_TYPE.OUTPUT:
                bits, stat = container.get_archive(file.mount_path)

                # create a tar file from the bits
                tar_file = tarfile.open(fileobj=io.BytesIO(b"".join(bits)), mode="r")
                # get the first file in the tar file
                tar_info = tar_file.next()
                # read the file
                output_files[file.name] = tar_file.extractfile(tar_info).read()

        return output_files

    def get_logs(self, job_handle):
        """
        Given a container id, return its logs as a string
        """
        client = self.docker_client
        container = client.containers.get(job_handle)
        return container.logs().decode()

    def cancel(self, job_handle):
        """
        Given a container id, cancel the container
        """
        client = self.docker_client
        container = client.containers.get(job_handle)
        container.stop()

    def cleanup(self, job_handle):
        """
        Given a container id, delete the container
        """
        client = self.docker_client
        container = client.containers.get(job_handle)
        container.remove()
