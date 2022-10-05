# local runtime for trac using docker
import csv
import json
import os
import tempfile
from functools import lru_cache

import docker


class RuntimeFactory:

    runtime = None

    @classmethod
    def get_runtime(cls, runtime_type="local"):
        if runtime_type == "local":
            # return a singleton
            if not cls.runtime:
                cls.runtime = LocalRuntime()
            return cls.runtime
        else:
            raise Exception("Runtime type not supported")


class LocalRuntime:
    def __init__(self) -> None:
        self.client = docker.from_env()

    @lru_cache(maxsize=128)
    def validate_image_exists(self, image_name, image_tag):
        image_name = image_name + ":" + image_tag

        # check if image exists locally
        # if not try pull the image and see if it exists
        # if not raise an exception
        try:
            image = self.client.images.get(image_name)
            if image:
                return True
            self.client.images.pull(image_name)
        except docker.errors.ImageNotFound:
            raise Exception("The docker image does not exist")
        except docker.errors.APIError:
            raise Exception("The docker image does not exist")

        return True

    def run(self, image_name, image_tag, parameters, dataset):
        image_name = image_name + ":" + image_tag

        temp_dir = tempfile.TemporaryDirectory()
        print(f"temp_dir: {temp_dir.name}")

        mount = {}

        # create temp_dir/output
        output_dir = temp_dir.name + "/output"
        os.makedirs(output_dir)
        # change the permission to 777
        os.chmod(output_dir, 0o777)

        # mount temp_dir/output to /output
        mount[temp_dir.name + "/output"] = {
            "bind": "/output",
            "mode": "rw",
        }

        # save the parameters as a json fil under temp_dir
        with open(temp_dir.name + "/parameters.json", "w") as f:
            json.dump(parameters, f)

        # mount temp_dir/parameters.json to /parameters.json
        mount[temp_dir.name + "/parameters.json"] = {
            "bind": "/parameters.json",
            "mode": "ro",
        }

        input_schema = self.schema(image_name.split(":")[0], image_tag)["input_schema"]
        for resource_schema in input_schema:
            resource_name = resource_schema["title"]
            # get the resources from the dataset
            resources = dataset.resources.filter(resource_type=resource_name)

            # save the resources as a csv file under temp_dir
            # replace the last _ in resource_name with a . as csv files are named with . instead of _

            file_name = resource_name.replace("_", ".", 1)
            with open(temp_dir.name + "/" + file_name, "w") as f:
                writer = csv.writer(f)
                # write the header
                writer.writerow(resource_schema["properties"].keys())
                # write the data
                for resource in resources:
                    writer.writerow(resource.value.values())

            # mount temp_dir/file_name to _mount_path
            mount_path = resource_schema["_mount_path"]
            # decide if mount_path is absolute or relative
            # if relative then mount to /workspace/{mount_path}
            if mount_path.startswith("/"):
                mount_path = mount_path
            else:
                mount_path = "/workspace/" + mount_path

            mount[temp_dir.name + "/" + file_name] = {"bind": mount_path, "mode": "rw"}

        # run the image
        command = (
            "-- run --parameters-path /parameters.json --output /output/output.ipynb"
        )
        container = self.client.containers.run(
            image_name, command=command, volumes=mount, detach=True
        )
        # stream the logs
        for line in container.logs(stream=True):
            print(line)

        # read the output.ipynb file
        with open(temp_dir.name + "/output/output.ipynb", "r") as f:
            return json.load(f)

    @lru_cache(maxsize=128)
    def spec(self, image_name, image_tag):
        image_name = image_name + ":" + image_tag

        # run the image with the spec command
        # parse the stdout as json from the container run
        logs = self.client.containers.run(image_name, "-- spec", remove=True)

        # parse the log as json
        spec = json.loads(logs.decode("utf-8"))
        return spec

    @lru_cache(maxsize=128)
    def schema(self, image_name, image_tag):
        image_name = image_name + ":" + image_tag

        logs = self.client.containers.run(image_name, "-- schema", remove=True)

        schema = json.loads(logs.decode("utf-8"))
        return schema
