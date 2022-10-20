# functions to build a runnable app image from a folder that contains a
# app spec file (trac.json)

# TODO: we should write a buildpack instead of a script file

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..schema.task import AppDef

MY_PATH = Path(__file__).parent.resolve()


def build_app_image(folder, image_name, clear_cache):
    """
    Build a runnable app image from a folder.
    The folder needs to contain a trac.json file (app spec file) in it.
    """

    # resolve the folder path
    folder = Path(folder).resolve()

    if isinstance(folder, str):
        folder = Path(folder)

    # check if the folder exists
    if not folder.exists():
        raise Exception(f"Folder {folder} does not exist")

    # check if the folder is a directory
    if not folder.is_dir():
        raise Exception(f"{folder} is not a directory")

    # check if the folder contains a trac.json file
    if not (folder / "trac.json").exists():
        raise Exception(f"{folder} does not contain a trac.json file")

    # copy the folder to a temp folder
    with tempfile.TemporaryDirectory() as tmpdir:
        # copy the contents of the folder to the temp folder
        shutil.copytree(folder, tmpdir, dirs_exist_ok=True)

        # copy the launcher.py to the temp folder
        shutil.copy(MY_PATH / "resources/launcher.py", tmpdir)

        # copy the entrypoint.sh to the temp folder
        shutil.copy(MY_PATH / "resources/entrypoint.sh", tmpdir)

        # write a Procfile to the temp folder
        with open(f"{tmpdir}/Procfile", "w") as f:
            f.write("web: ./entrypoint.sh")

        # ls the temp folder
        subprocess.run(["ls", "-l", tmpdir])

        # read the trac.json file
        app_spec = json.load(open(Path(folder) / "trac.json"))

        # validate trac.json against the app spec schema
        try:
            AppDef.validate(app_spec)
        except Exception as e:
            raise Exception(f"Invalid app spec file: {e}")

        app_name = app_spec["name"]

        # slugify the app name
        app_name = app_name.replace(" ", "_").lower()

        if not image_name:
            image_name = app_name

        # replace trac.json's handler field with container field
        for task_spec in app_spec["tasks"]:
            task_name = task_spec["name"]
            task_spec["container"] = {
                "image": image_name,
                "tag": "latest",
                "args": [
                    " -- ",
                    "run",
                    f"{task_name}",
                ],
            }

        # write the trac.json file to the temp folder
        with open(f"{tmpdir}/trac.json", "w") as f:
            json.dump(app_spec, f, indent=4)

        # call the buildpacks to build the image
        # check if "pack" command is installed, if not, throw an error
        res = shutil.which("pack")
        if res is None:
            # print the installation instructions
            print("Buildpacks is not installed")
            print("Please install buildpacks by following the instructions here:")
            print("https://buildpacks.io/docs/tools/pack/install-pack/")
            raise Exception("Buildpacks is not installed")

        # call paketo python buildpacks to build the image
        command = [
            "pack",
            "build",
            image_name,
            "--buildpack",
            "gcr.io/paketo-buildpacks/python",
            "--builder",
            "docker.io/paketobuildpacks/builder:base",
            "--path",
            tmpdir,
        ]

        if clear_cache:
            command.append("--clear-cache")

        # run the command and stream the output
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        while True:
            output = process.stdout.readline()
            if output == b"" and process.poll() is not None:
                break
            if output:
                print(output.strip().decode("utf-8"))

        # report any errors

        if process.returncode != 0:
            raise Exception("Error building the image")

        # print the image name
        print(f"Image {image_name} built successfully")
        print(f"Run the image with the following command:")
        print(f"docker run --rm {image_name} -- --help")

        return image_name, "latest"
