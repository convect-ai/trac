# utils functions to run docker containers locally

import json
from functools import lru_cache
from typing import List, Union

import docker
from trac.schema.task import FILE_TYPE, AppDef, FileDef, ParameterDef, TaskDef


class DockerUtils:

    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = docker.from_env()
        return cls._client

    @classmethod
    @lru_cache(maxsize=128)
    def valudate_image_exists(cls, image_name, image_tag) -> bool:
        image_name = image_name + ":" + image_tag

        # check if image exists locally
        # if not try pull the image and see if it exists
        # if not raise an exception

        try:
            image = cls.get_client().images.get(image_name)
            if image:
                return True
            cls.get_client().images.pull(image_name)

        except docker.errors.ImageNotFound:
            raise Exception("The docker image does not exist")
        except docker.errors.APIError:
            raise Exception("The docker image does not exist")

        return True

    @classmethod
    @lru_cache
    def spec(cls, image_name, image_tag, task_name=None) -> Union[TaskDef, AppDef]:
        """
        Return the spec of the app
        """
        client = cls.get_client()
        image_name = image_name + ":" + image_tag

        # create a container and run it with command "-- spec"
        # get the output and return it

        if not task_name:
            command = "-- spec"
        else:
            command = f"-- spec --task-name {task_name}"

        logs = client.containers.run(
            image_name,
            command=command,
            auto_remove=True,
        )

        print(logs)

        # get the output
        output = logs.decode("utf-8")

        try:
            spec = json.loads(output)
        except json.decoder.JSONDecodeError as ex:
            print(f"Error: {ex}")
            raise Exception("The app spec is not valid")

        if not task_name:
            return AppDef.parse_obj(spec)
        else:
            return TaskDef.parse_obj(spec)

    @classmethod
    @lru_cache
    def tasks(cls, image_name, image_tag) -> List[str]:
        """
        Return the tasks of the app
        """
        client = cls.get_client()
        image_name = image_name + ":" + image_tag

        # create a container and run it with command "-- tasks"
        # get the output and return it

        logs = client.containers.run(
            image_name,
            command="-- tasks",
            auto_remove=True,
        )

        # get the output
        output = logs.decode("utf-8")

        # each line is a task
        tasks = output.splitlines()
        return tasks

    @classmethod
    @lru_cache
    def input_schema(cls, image_name, image_tag, task_name) -> List[FileDef]:
        """
        Return the input schema of a task
        """

        spec = cls.spec(image_name, image_tag, task_name)

        return [f for f in spec.io.files if f.type == FILE_TYPE.INPUT]

    @classmethod
    @lru_cache
    def output_schema(cls, image_name, image_tag, task_name) -> List[FileDef]:
        """
        Return the output schema of a task
        """

        spec = cls.spec(image_name, image_tag, task_name)

        return [f for f in spec.io.files if f.type == FILE_TYPE.OUTPUT]

    @classmethod
    @lru_cache
    def parameter_schema(cls, image_name, image_tag, task_name) -> List[ParameterDef]:
        """
        Return the parameter schema of a task
        """

        spec = cls.spec(image_name, image_tag, task_name)

        return spec.parameter.parameters
